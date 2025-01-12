import discord
import logging
import os
import mysql.connector

from dotenv import load_dotenv
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

load_dotenv(".env", override=True)
ROLE_TO_VERIFY = os.getenv('ROLE_ID')
VERIFICATION = os.getenv('VERIFICATION', 'false').strip().lower() == "true"
if VERIFICATION:
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USERNAME = os.getenv('MYSQL_USERNAME', '')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', '')
else:
    logging.info("Verification disabled")

db_connection = None

def init_db():
    """
    Initialize the database connection.
    """
    global db_connection
    if db_connection is None:
        try:
            db_connection = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USERNAME,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            logging.info("Database connection established.")
        except Exception as e:
            logging.error(f"An error occurred during database connection: {e}")
            db_connection = None
    return db_connection


class Verify(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.roles = int(ROLE_TO_VERIFY)
        self.db = init_db()
        
    
    async def update_roles_in_db(self, guild: discord.Guild):
        """
        Efficiently updates the roles in the database.
        """
        if self.db is None:
            logging.error("Database connection failed. Cannot update roles.")
            return
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT guild_role_id FROM roles")
                existing_role_ids = set(int(row[0]) for row in cursor)
                guild_role_ids = set(role.id for role in guild.roles)
                new_role_ids = guild_role_ids - existing_role_ids
                for role in guild.roles:
                    if role.id in new_role_ids:
                        cursor.execute(
                            "INSERT INTO roles (role_name, guild_role_id) VALUES (%s, %s)",
                            (role.name, role.id)
                        )
                        logging.info(f"Inserted role {role.name} with ID {role.id}")
                removed_role_ids = existing_role_ids - guild_role_ids
                if removed_role_ids:
                    removed_role_ids = tuple(removed_role_ids)
                    placeholders = ', '.join(['%s'] * len(removed_role_ids))
                    query = f"DELETE FROM roles WHERE guild_role_id IN ({placeholders})"
                    cursor.execute(
                        query, removed_role_ids
                    )
                    logging.info(f"Removed roles with IDs: {', '.join(map(str, removed_role_ids))}")
                
                self.db.commit()
        except Exception as e:
            logging.error(f"Error updating roles: {e}")
            self.db.rollback()
    
    
    async def update_users_in_db(
        self, ctx, guild: discord.Guild,
        real_name: str, student_id: str, role: str):
        
        if self.db is None:
            logging.error("Database connection failed. Cannot update users.")
            if ctx:
                await ctx.send("Database connection failed. Please try again later.")
            return

        try:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT * FROM roles WHERE role_name = %s", (role,))
                role_data = cursor.fetchone()
                if role_data is None:
                    logging.error(f"Role '{role}' not found in the database.")
                    if ctx:
                        await ctx.send(f"Role '{role}' not found in the database.")
                    return
                guild_role_id = role_data[1]

            with self.db.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE student_id = %s", (student_id,))
                user_data = cursor.fetchone()
                if user_data is None:
                    logging.error(f"User with student ID {student_id} not found in the database.")
                    if ctx:
                        await ctx.send(f"User with student ID {student_id} not found.")
                    return

                cursor.execute(
                    """UPDATE users
                    SET real_name = %s, guild_role_id = %s WHERE student_id = %s""",
                    (real_name, guild_role_id, student_id)
                )
                self.db.commit()

            logging.info(f"User updated successfully.")
            if ctx:
                await ctx.send(f"User updated successfully in the database.")

        except Exception as e:
            logging.error(f"Error updating user in the database: {e}")
            self.db.rollback()
            if ctx:
                await ctx.send("An error occurred while updating the user. Please try again later.")


    async def create_users_in_db(
        self, ctx, guild: discord.Guild,
        real_name: str, student_id: str, role: str, registered: bool):
        """
        Create a user in the database with the given details.

        Args:
            ctx: The context of the command.
            guild: The Discord guild (server).
            real_name: The real name of the user.
            student_id: The student's ID.
            role: The role name.
            registered: Registration status of the user.
        """
        if self.db is None:
            logging.error("Database connection failed. Cannot update users.")
            if ctx:
                await ctx.respond("Database connection failed. Please try again later.", ephemeral=True)
            return

        try:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT * FROM roles WHERE role_name = %s", (role,))
                role_data = cursor.fetchone()

                if not role_data:
                    error_message = f"Role '{role}' not found in the database."
                    logging.error(error_message)
                    if ctx:
                        await ctx.send(error_message)
                    return
                
                guild_role_id = role_data[1]

            with self.db.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE student_id = %s", (student_id,))
                user_data = cursor.fetchone()

                if user_data:
                    error_message = f"User with student ID {student_id} already exists in the database."
                    logging.error(error_message)
                    if ctx:
                        await ctx.respond(error_message, emphemeral=True)
                    return

                # Insert new user
                cursor.execute(
                    """INSERT INTO users (real_name, student_id, guild_role_id, registered)
                    VALUES (%s, %s, %s, %s)""",
                    (real_name, student_id, str(guild_role_id), registered)
                )
                self.db.commit()

            success_message = f"User '{real_name}' with student ID {student_id} has been successfully added."
            logging.info(success_message)
            if ctx:
                await ctx.respond(success_message, emphemeral=True)

        except Exception as e:
            logging.error(f"Error while creating user in the database: {e}")
            self.db.rollback()
            if ctx:
                await ctx.respond("An error occurred while creating the user. Please try again later.", emphemeral=True)


    async def verify_user(
        self, ctx, guild: discord.Guild, real_name: str, student_id: str, discord_id: str, discord_user: str
    ):
        """
        Verify a user in the database.

        Args:
            ctx: The context of the command.
            guild: The Discord guild (server).
            student_id: The student's ID to verify.
            discord_id: The Discord user ID of the member.
            discord_user: The Discord username of the member.
        """
        if self.db is None:
            logging.error("Database connection failed. Cannot verify user.")
            if ctx:
                await ctx.respond("Database connection failed. Please try again later.", ephemeral=True)
            return

        try:
            with self.db.cursor() as cursor:
                # Check if the Discord user is already associated with any student_id
                cursor.execute(
                    "SELECT * FROM users WHERE discord_id = %s OR discord_username = %s",
                    (discord_id, discord_user),
                )
                existing_user = cursor.fetchone()

                if existing_user:
                    error_message = (
                        "This Discord account is already verified. "
                        "You cannot verify again."
                    )
                    logging.error(error_message)
                    if ctx:
                        await ctx.respond(error_message, ephemeral=True)
                    return

                # Check if the user exists in the database and is unregistered
                cursor.execute(
                    "SELECT * FROM users WHERE student_id = %s AND registered = FALSE AND real_name = %s",
                    (student_id, real_name),
                )
                user_data = cursor.fetchone()

                if user_data:
                    # Update the user with Discord details and mark as registered
                    cursor.execute(
                        """
                        UPDATE users 
                        SET discord_id = %s, discord_username = %s, registered = %s 
                        WHERE student_id = %s AND real_name = %s
                        """,
                        (discord_id, discord_user, True, student_id, real_name),
                    )
                    self.db.commit()

                    # Assign the verified role to the user in Discord
                    verified_role = guild.get_role(self.roles)
                    if verified_role:
                        member = guild.get_member(int(discord_id))
                        if member:
                            await member.add_roles(verified_role)
                            success_message = f"User with student ID {student_id} has been successfully verified."
                            logging.info(success_message)
                            if ctx:
                                await ctx.respond(success_message, ephemeral=True)
                        else:
                            logging.error(f"Discord member with ID {discord_id} not found in the guild.")
                            if ctx:
                                await ctx.respond(
                                    "Unable to add roles. User not found in the guild.", ephemeral=True
                                )
                    else:
                        logging.error("Verified role not found.")
                        if ctx:
                            await ctx.respond(
                                "Verified role not found. Please contact an administrator.", ephemeral=True
                            )
                else:
                    error_message = f"No unregistered user found with student ID {student_id} and real name {real_name}."
                    logging.error(error_message)
                    if ctx:
                        await ctx.respond(error_message, ephemeral=True)
        except Exception as e:
            logging.error(f"Error while verifying user: {e}")
            self.db.rollback()
            if ctx:
                await ctx.respond(
                    "An error occurred while verifying the user. Please try again later.", ephemeral=True
                )
                
                
    @commands.slash_command(
        name='update-roles-db',
        description='Update the roles in the database.',
        default_member_permissions=discord.Permissions(administrator=True),
    )
    @commands.has_permissions(administrator=True)
    async def update_roles_db(self, ctx: discord.ApplicationContext):
        try:
            guild = ctx.guild
            await self.update_roles_in_db(guild)
            await ctx.respond("Roles have been updated in the database!", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"An error occurred while updating roles: {e}", ephemeral=True)


    @commands.slash_command(
        name='update-users-db',
        description='Update the users in the database.',
        default_member_permissions=discord.Permissions(administrator=True),
    )
    @commands.has_permissions(administrator=True)
    @commands.check(lambda ctx: VERIFICATION)
    async def update_users_db(self, ctx: discord.ApplicationContext, real_name: str, student_id: str, role: str):
        try:
            guild = ctx.guild
            await self.update_users_in_db(ctx, guild, real_name, student_id, role)
            await ctx.respond("Users have been updated in the database!", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"An error occurred while updating users: {e}", ephemeral=True)


    @commands.slash_command(
        name='create-users-db',
        description='Create the users in the database.',
        default_member_permissions=discord.Permissions(administrator=True),
    )
    @commands.has_permissions(administrator=True)
    @commands.check(lambda ctx: VERIFICATION)
    async def create_users_db(self, ctx: discord.ApplicationContext, real_name: str, student_id: str, role: str, registered: bool = False):
        try:
            guild = ctx.guild
            await self.create_users_in_db(ctx, guild, real_name, student_id, role, registered)
            await ctx.respond("Users have been created in the database!", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"An error occurred while creating users: {e}", ephemeral=True)


    @commands.slash_command(
        name='verify',
        description='Không xác thực thì có cái nịt',
    )
    @commands.check(lambda ctx: VERIFICATION)
    async def verify(self, ctx: discord.ApplicationContext, real_name:str ,student_id: str):
        try:
            guild = ctx.guild
            await self.verify_user(ctx, guild, real_name,student_id, str(ctx.author.id), str(ctx.author))
        except Exception as e:
            await ctx.respond(f"An error occurred while verify users: {e}", ephemeral=True)
            
            
    @verify.error
    async def verify_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            logging.error("Verify command failed due to missing permissions.")
        else:
            logging.error(f"An error occurred during verification: {error}")

    
def setup(bot):
    bot.add_cog(Verify(bot))
