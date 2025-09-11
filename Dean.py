import discord 
from discord.ext import commands 
import asyncio
from datetime import datetime, timedelta
import os

#Global Variables
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
pool_cooldowns = {}
previous_poll={} 
bot_key = os.getenv("DISCORD_MAIN_BOT_TOKEN")

#C like Macros
VOTE_THRESHOLD = 5
ERROR_ADMIN_ID = 1405195061162934293 
POLL_COOLDOWN_SECONDS = 86000

#Bot logs onto any server, ready to use
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")

#Poll method, allows the user to create a secure poll 
@bot.command()
async def poll(ctx, user: discord.Member, *, friend_name: str):
    await ctx.message.delete()
    author_id = ctx.author.id
    if author_id in pool_cooldowns:
        last_poll_time = pool_cooldowns[author_id]
        cooldown_end_time = last_poll_time + timedelta(seconds=POLL_COOLDOWN_SECONDS) 
        if datetime.utcnow() < cooldown_end_time:
            time_remaining = cooldown_end_time - datetime.utcnow()
            hours, remainder = divmod(time_remaining.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.send(f"You are on a cooldown."
                           f"Please wait {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds" 
                           f"before starting a new poll.")
            return


    poll_message = await create_poll(ctx, user, friend_name)
    previous_poll[ctx.guild.id] = poll_message
    previous_poll[ctx.guild.id] = {"message": poll_message, "author_id": author_id} 
    pool_cooldowns[author_id] = datetime.utcnow()
    yes_votes, no_votes = await poll_monitor(ctx, poll_message)
    await check_poll_results(ctx, yes_votes, no_votes, user)

#Manual send method, if the poll invite fails to send to the user, admin can send invite themselves
@bot.command()
@commands.has_permissions(administrator=True)
async def manualsend(ctx, user: discord.Member):
    ctx.send(f"Manually sending invite to {user.name}")
    await send_invite(ctx, user)

#Error handling the manual send method
@manualsend.error
async def manualsend_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Could not find that user. Please mention the user or provide a valid user ID.")
    else:
        await ctx.send("An error occurred while processing the command.")

#Deletepoll method, allows user to delete a poll if needed, cooldown will be 0
@bot.command()
@commands.has_permissions(administrator=True)
async def deletepoll(ctx):
    await ctx.message.delete()
    guild_id = ctx.guild.id
    if guild_id in previous_poll and previous_poll[guild_id] is not None:
        try:
             poll_info = previous_poll[guild_id]
             poll_author_id = poll_info["author_id"]
             poll_message = poll_info["message"]
             await poll_message.delete()
             await ctx.send("Poll message deleted successfully.", delete_after=10)
             if poll_author_id in pool_cooldowns:
                del pool_cooldowns[poll_author_id]
             previous_poll[guild_id] = None
        except discord.NotFound:
            await ctx.send("Poll message not found. It may have already been deleted.", delete_after=10)
            previous_poll.pop(guild_id, None)
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete the poll message.", delete_after=10)
        except Exception as e:
            await ctx.send(f"An error occurred while deleting the poll message: {e}", delete_after=10)
    else:
        await ctx.send("No poll message found to delete.", delete_after=10) 

@deletepoll.error
async def deletepoll_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
    else:
        await ctx.send("An error occurred while processing the command.")

#Allows the bot to send the creator of the invite poll an invite to the server
async def send_invite(ctx, user):
    dm_message = " "
    error_message = f"Could not send invite to {user.name}, this API mad dihh"
    try:
        invite = await ctx.channel.create_invite(max_age=300, max_uses=1)
        dm_message = (f"Hello {user.name}, the poll to invite your friend has passed! "
                      f"Here is your invite link: {invite}, please send it to your friend, it expires in 5 minutes."
                    )
    
        await user.send(dm_message)
        await ctx.send(f"Invite sent to {user.name}.")
    except discord.Forbidden:
        await ctx.send(error_message)
        await notify_admin(ctx, error_message)
    except discord.HTTPException as e:
        await ctx.send(f"I failed to create invite link: {e}, this API sucks mad dihh")
        await notify_admin(ctx, error_message) 

#Allows the bot to check if the votes are valid
def poll_reaction_check(poll_message_id, reaction, reactor):
    reaction_check = reaction.message.id == poll_message_id and str(reaction.emoji) in ["✅", "❌"] and not reactor.bot
    return reaction_check

#Creates the poll
async def create_poll(ctx, user: discord.User, friend_name : str):
    poll_message = await ctx.send(
        f"{user.mention}, would like to invite {friend_name} " 
        f"to the server? React with ✅ to accept or ❌ to decline."
    )
    await poll_message.add_reaction("✅")
    await poll_message.add_reaction("❌")
    return poll_message

#Adds and Removes reactions based on user feedback
async def poll_monitor(ctx, poll_message):
    yes_votes = set()
    no_votes = set()
    check = lambda reaction, reactor: poll_reaction_check(poll_message.id, reaction, reactor)
    
    while True:
        try:
            reaction, reactor = await bot.wait_for("reaction_add", timeout=10800, check=check)
            if str(reaction.emoji) == "✅":
                yes_votes.add(reactor.id)
                if reactor.id in no_votes:
                    no_votes.discard(reactor.id)
                    await poll_message.remove_reaction("❌", reactor)
            elif str(reaction.emoji) == "❌":
                no_votes.add(reactor.id)
                if reactor.id in yes_votes:
                    yes_votes.discard(reactor.id) 
                    await poll_message.remove_reaction("✅", reactor)
            
            if len(yes_votes) >= VOTE_THRESHOLD or len(no_votes) >= VOTE_THRESHOLD:
                break 
        except asyncio.TimeoutError:
            # If the poll runs for 24 hours (86400s) with no new votes, it will time out.
            await ctx.send("The poll has timed out due to inactivity.")
            break 
    return yes_votes, no_votes

#Always on, checks to see if any existing poll meets the preset threshold of votes
async def check_poll_results(ctx, yes_votes, no_votes, user: discord.User):
    yes_count = len(yes_votes)
    no_count = len(no_votes)
    result_message = " "

    if yes_count >= VOTE_THRESHOLD and yes_count > no_count:
        result_message = (f"The poll has conclcuded, community has voted to invite the new member!"
                          f"Results are ✅ {yes_count} - ❌ {no_count}. "
        )
        await ctx.send(result_message)
        await send_invite(ctx, user)
    elif len(no_votes) >= VOTE_THRESHOLD:
        result_message = (f"The poll has concluded, community has voted against inviting the new member! "
                          f"Results are ❌ {no_count} - ✅ {yes_count}. "
        )
        await ctx.send(result_message)
    else:
        await ctx.send("The poll did not reach the required number of votes to conclude.")

#Will notify an admin if there are any errors of sending an invite 
async def notify_admin(ctx, error_message: str):
    if not ERROR_ADMIN_ID:
        return 0
    try:
        admin_role = await ctx.guild.fetch_member(ERROR_ADMIN_ID)
        if admin_role:
            dm = (f"Bot error: {error_message}\n") 
            try:
                await admin_role.send(dm)
            except discord.Forbidden:
                print(f"Could not send DM to {admin_role.name}, check privacy settings.")
        else:
            print(f"Admin with ID {ERROR_ADMIN_ID} not found in the server.")
    except discord.NotFound:
        print(f"Admin with ID {ERROR_ADMIN_ID} not found.")
    except Exception as e:
        print(f"An error occurred while notifying the admin: {e}")


#Bot key, allowing the bot to run
if not bot_key:
    raise ValueError("Invalid Botkey")
bot.run(bot_key)

    

    