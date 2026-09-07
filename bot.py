import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import database
from config import RATES, CRYPTO, PAYMENT_METHODS


# =========================================================
# SETUP
# =========================================================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
PREFIX = "."

database.setup()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin():
    async def predicate(ctx):
        return (
            ctx.guild is not None
            and ctx.author.guild_permissions.administrator
        )

    return commands.check(predicate)


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():
    print("=" * 50)
    print("        WINTER EXCHANGE")
    print("=" * 50)
    print(f"Bot Login : {bot.user}")
    print(f"Bot ID    : {bot.user.id}")
    print(f"Servers   : {len(bot.guilds)}")
    print(f"Prefix    : {PREFIX}")
    print("=" * 50)
    print("Winter Exchange is ONLINE!")
    print("=" * 50)


# =========================================================
# HELP
# =========================================================

@bot.command(name="help")
@is_admin()
async def help_command(ctx):

    embed = discord.Embed(
        title="❄️ Winter Exchange",
        description=(
            "**Available Commands**\n\n"

            "**Ticket System**\n"
            "`.exchpanel #channel` — Send ticket panel\n"
            "`.exchlog #channel` — Set log channel\n"
            "`.deal` — Claim a ticket\n"
            "`.done` — Complete a ticket\n"
            "`.delete` — Delete a ticket\n"
            "`.reopen` — Reopen a ticket\n\n"

            "**Staff Roles**\n"
            "`.I2C @role` — INR → Crypto\n"
            "`.C2I @role` — Crypto → INR\n"
            "`.C2C @role` — Crypto → Crypto\n"
            "`.N2C @role` — NPR → Crypto\n"
            "`.C2N @role` — Crypto → NPR\n"
            "`.B2C @role` — BDT → Crypto\n"
            "`.C2B @role` — Crypto → BDT"
        ),
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed)


# =========================================================
# PANEL
# =========================================================

class RateButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Rates",
            style=discord.ButtonStyle.secondary,
            custom_id="winter_rates"
        )

    async def callback(self, interaction):

        text = (
            "**__INR Exchanges__**\n"
            f"> - **INR To Crypto: {RATES['I2C']} | Any Amount**\n"
            f"> - **Crypto To INR: {RATES['C2I']} | Any Amount**\n\n"

            "**__Crypto Exchanges__**\n"
            f"> - **Crypto To Crypto: {RATES['C2C']}**\n\n"

            "**__NPR Exchanges__**\n"
            f"> - **NPR To Crypto: {RATES['N2C']} | Any Amount**\n"
            f"> - **Crypto To NPR: {RATES['C2N']} | Any Amount**\n\n"

            "**__BDT Exchanges__**\n"
            f"> - **BDT To Crypto: {RATES['B2C']} | Any Amount**\n"
            f"> - **Crypto To BDT: {RATES['C2B']} | Any Amount**"
        )

        embed = discord.Embed(
            title="Winter Exchange Rates",
            description=text,
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


class CreateTicketButton(discord.ui.Button):

    def __init__(self):
        super().__init__(
            label="Create Ticket",
            style=discord.ButtonStyle.primary,
            custom_id="winter_create_ticket"
        )

    async def callback(self, interaction):

        await interaction.response.send_message(
            "### Currently you are Sending",
            view=CurrencyView(),
            ephemeral=True
        )


class PanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(CreateTicketButton())
        self.add_item(RateButton())


# =========================================================
# CURRENCY
# =========================================================

class CurrencySelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(
                label="INR",
                description="Indian Rupee"
            ),
            discord.SelectOption(
                label="NPR",
                description="Nepalese Rupee"
            ),
            discord.SelectOption(
                label="BDT",
                description="Bangladeshi Taka"
            ),
            discord.SelectOption(
                label="Crypto",
                description="Cryptocurrency"
            )
        ]

        super().__init__(
            placeholder="Select currency...",
            options=options,
            custom_id="winter_currency"
        )

    async def callback(self, interaction):

        source = self.values[0]

        if source == "Crypto":

            await interaction.response.edit_message(
                content="### Choose the Crypto you are sending",
                view=CryptoSendingView()
            )

        else:

            await interaction.response.edit_message(
                content="### Choose the app for Money Transfer",
                view=PaymentView(source)
            )


class CurrencyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(CurrencySelect())


# =========================================================
# PAYMENT METHODS
# =========================================================

class PaymentSelect(discord.ui.Select):

    def __init__(self, source):

        self.source = source

        options = [
            discord.SelectOption(label=x)
            for x in PAYMENT_METHODS[source]
        ]

        super().__init__(
            placeholder="Choose payment app...",
            options=options
        )

    async def callback(self, interaction):

        payment = self.values[0]

        await interaction.response.edit_message(
            content="### Choose the Crypto you will be receiving",
            view=ReceivingCryptoView(
                self.source,
                payment,
                None
            )
        )


class PaymentView(discord.ui.View):

    def __init__(self, source):
        super().__init__(timeout=300)
        self.add_item(PaymentSelect(source))


# =========================================================
# CRYPTO SENDING
# =========================================================

class SendingCryptoSelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(label=x)
            for x in CRYPTO
        ]

        super().__init__(
            placeholder="Choose crypto...",
            options=options
        )

    async def callback(self, interaction):

        crypto = self.values[0]

        await interaction.response.edit_message(
            content="### Choose the Crypto you will be receiving",
            view=ReceivingCryptoView(
                "CRYPTO",
                None,
                crypto
            )
        )


class CryptoSendingView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(SendingCryptoSelect())


# =========================================================
# RECEIVING CRYPTO
# =========================================================

class ReceivingCryptoSelect(discord.ui.Select):

    def __init__(
        self,
        source,
        payment,
        sending_crypto
    ):

        self.source = source
        self.payment = payment
        self.sending_crypto = sending_crypto

        options = [
            discord.SelectOption(label=x)
            for x in CRYPTO
        ]

        super().__init__(
            placeholder="Choose receiving crypto...",
            options=options
        )

    async def callback(self, interaction):

        receiving_crypto = self.values[0]

        await interaction.response.edit_message(
            content=(
                "### Enter your amount\n\n"
                "**Amount:** `0`"
            ),
            view=KeypadView(
                self.source,
                self.payment,
                self.sending_crypto,
                receiving_crypto
            )
        )


class ReceivingCryptoView(discord.ui.View):

    def __init__(
        self,
        source,
        payment,
        sending_crypto
    ):

        super().__init__(timeout=300)

        self.add_item(
            ReceivingCryptoSelect(
                source,
                payment,
                sending_crypto
            )
        )


# =========================================================
# KEYPAD
# =========================================================

class KeypadView(discord.ui.View):

    def __init__(
        self,
        source,
        payment,
        sending_crypto,
        receiving_crypto
    ):

        super().__init__(timeout=300)

        self.source = source
        self.payment = payment
        self.sending_crypto = sending_crypto
        self.receiving_crypto = receiving_crypto

        self.amount = ""

        numbers = [
            "1", "2", "3",
            "4", "5", "6",
            "7", "8", "9",
            ".", "0"
        ]

        for number in numbers:

            button = discord.ui.Button(
                label=number,
                style=discord.ButtonStyle.secondary
            )

            button.callback = self.number_callback(number)

            self.add_item(button)

        backspace = discord.ui.Button(
            label="⌫",
            style=discord.ButtonStyle.danger
        )

        backspace.callback = self.delete_callback
        self.add_item(backspace)

        confirm = discord.ui.Button(
            label="Confirm",
            style=discord.ButtonStyle.success,
            row=4
        )

        confirm.callback = self.confirm_callback
        self.add_item(confirm)

    def number_callback(self, number):

        async def callback(interaction):

            if len(self.amount) >= 15:
                await interaction.response.defer()
                return

            if number == "." and "." in self.amount:
                await interaction.response.defer()
                return

            self.amount += number

            await interaction.response.edit_message(
                content=(
                    "### Enter your amount\n\n"
                    f"**Amount:** `{self.amount or '0'}`"
                ),
                view=self
            )

        return callback

    async def delete_callback(self, interaction):

        self.amount = self.amount[:-1]

        await interaction.response.edit_message(
            content=(
                "### Enter your amount\n\n"
                f"**Amount:** `{self.amount or '0'}`"
            ),
            view=self
        )

    async def confirm_callback(self, interaction):

        if not self.amount:

            await interaction.response.send_message(
                "❌ Please enter an amount.",
                ephemeral=True
            )
            return

        try:
            amount = float(self.amount)

            if amount <= 0:
                raise ValueError

        except ValueError:

            await interaction.response.send_message(
                "❌ Invalid amount.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            content="⏳ Creating your ticket...",
            view=None
        )

        await create_ticket(
            interaction,
            self.source,
            self.payment,
            self.sending_crypto,
            self.receiving_crypto,
            amount
        )


# =========================================================
# EXCHANGE TYPE
# =========================================================

def get_exchange_type(source):

    if source == "INR":
        return "I2C"

    if source == "NPR":
        return "N2C"

    if source == "BDT":
        return "B2C"

    return "C2C"


# =========================================================
# CREATE TICKET
# =========================================================

async def create_ticket(
    interaction,
    source,
    payment,
    sending_crypto,
    receiving_crypto,
    amount
):

    guild = interaction.guild

    exchange_type = get_exchange_type(source)

    counter = database.get_setting("ticket_counter")

    if counter is None:
        number = 1
    else:
        number = int(counter) + 1

    database.set_setting(
        "ticket_counter",
        number
    )

    role_id = database.get_setting(
        f"role_{exchange_type}"
    )

    overwrites = {
        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        interaction.user:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
    }

    if role_id:

        role = guild.get_role(int(role_id))

        if role:

            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

    category = discord.utils.get(
        guild.categories,
        name="Winter Tickets"
    )

    if category is None:

        category = await guild.create_category(
            "Winter Tickets"
        )

    channel = await guild.create_text_channel(
        f"{exchange_type.lower()}-{number:03d}",
        category=category,
        overwrites=overwrites
    )

    database.create_ticket(
        channel.id,
        number,
        interaction.user.id,
        exchange_type,
        source,
        payment,
        sending_crypto,
        receiving_crypto,
        amount
    )

    embed = discord.Embed(
        title="Exchange Details",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="From",
        value=f"{amount:g} {source}",
        inline=False
    )

    embed.add_field(
        name="Receiving Crypto",
        value=receiving_crypto,
        inline=False
    )

    if payment:
        embed.add_field(
            name="Payment Method",
            value=payment,
            inline=False
        )

    if sending_crypto:
        embed.add_field(
            name="Sending Crypto",
            value=sending_crypto,
            inline=False
        )

    embed.add_field(
        name="Exchange Type",
        value=exchange_type,
        inline=False
    )

    embed.add_field(
        name="Customer",
        value=interaction.user.mention,
        inline=False
    )

    embed.set_footer(
        text=f"Winter Exchange • Ticket #{number:03d}"
    )

    await channel.send(
        embed=embed
    )

    safety = discord.Embed(
        title="⚠️ Transaction Safety",
        description=(
            "For your safety, always complete transactions "
            "within your ticket, where funds are securely "
            "held for both parties.\n\n"
            "> - We are not responsible for any losses or "
            "scams resulting from transactions conducted "
            "outside the ticket system.\n"
            "> - Anyone asking you to move the trade outside "
            "the ticket is very likely attempting to scam you."
        ),
        color=discord.Color.orange()
    )

    await channel.send(
        embed=safety,
        view=TicketView()
    )

    await interaction.edit_original_response(
        content=f"✅ Ticket created: {channel.mention}",
        view=None
    )


# =========================================================
# TICKET BUTTONS
# =========================================================

class ClaimButton(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Claim Ticket",
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction):

        ticket = database.get_ticket(
            interaction.channel.id
        )

        if not ticket:
            await interaction.response.send_message(
                "❌ This isn't a Winter Exchange ticket.",
                ephemeral=True
            )
            return

        role_id = database.get_setting(
            f"role_{ticket[4]}"
        )

        if role_id:

            role = interaction.guild.get_role(
                int(role_id)
            )

            if role and role not in interaction.user.roles:

                await interaction.response.send_message(
                    "❌ You don't have the required exchanger role.",
                    ephemeral=True
                )
                return

        if ticket[10]:

            await interaction.response.send_message(
                "❌ This ticket is already claimed.",
                ephemeral=True
            )
            return

        database.claim_ticket(
            interaction.channel.id,
            interaction.user.id
        )

        await interaction.channel.send(
            f"🔒 Ticket claimed by {interaction.user.mention}"
        )

        await interaction.response.send_message(
            "✅ You claimed this ticket.",
            ephemeral=True
        )


class DoneButton(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Done",
            style=discord.ButtonStyle.success
        )

    async def callback(self, interaction):

        ticket = database.get_ticket(
            interaction.channel.id
        )

        if not ticket:

            await interaction.response.send_message(
                "❌ This isn't a Winter Exchange ticket.",
                ephemeral=True
            )
            return

        if not ticket[10]:

            await interaction.response.send_message(
                "❌ This ticket hasn't been claimed.",
                ephemeral=True
            )
            return

        if ticket[10] != interaction.user.id:

            await interaction.response.send_message(
                "❌ Only the exchanger who claimed this "
                "ticket can complete it.",
                ephemeral=True
            )
            return

        database.close_ticket(
            interaction.channel.id
        )

        await interaction.response.send_message(
            "✅ Exchange completed. Ticket closed."
        )


class TicketView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(ClaimButton())
        self.add_item(DoneButton())


# =========================================================
# EXCHANGE PANEL COMMAND
# =========================================================

@bot.command()
@is_admin()
async def exchpanel(ctx, channel: discord.TextChannel):

    embed = discord.Embed(
        title="Winter Ticket Panel",
        description=(
            "# `Winter Exchanges`\n\n"
            "> Creating a ticket means you accept our "
            "terms and conditions.\n\n"

            "> **Click on the buttons to Interact**\n"
            "> - Create Ticket - Open a Exchange ticket\n"
            "> - Rate - Check current exchange rates\n\n"

            "### NOTE:\n"
            "> - Third-party payments are strictly prohibited.\n"
            "> - We do not cover transaction fees.\n"
            "> - Preferring Wallet Payment "
            "( Eg . Dhani , Nye , Mbk, omni , Fampay, "
            "UPI LITE ) etc\n\n"

            "> - Do not pay more than the exchanger's "
            "stated limit.\n"
            "> - Do not proceed with the deal until the "
            "exchanger has claimed the ticket and the "
            "ticket has been renamed.\n"
            "> - We Won't be liable and won't refund if "
            "paid the exchanger above his limit directly "
            "without mm"
        ),
        color=discord.Color.blurple()
    )

    await channel.send(
        embed=embed,
        view=PanelView()
    )

    await ctx.send(
        f"✅ Panel sent to {channel.mention}",
        delete_after=5
    )


# =========================================================
# EXCHANGE LOG
# =========================================================

@bot.command()
@is_admin()
async def exchlog(ctx, channel: discord.TextChannel):

    database.set_setting(
        "log_channel",
        channel.id
    )

    await ctx.send(
        f"✅ Exchange log channel set to {channel.mention}"
    )


# =========================================================
# ROLE COMMANDS
# =========================================================

async def set_role(ctx, exchange_type, role):

    database.set_setting(
        f"role_{exchange_type}",
        role.id
    )

    await ctx.send(
        f"✅ `{exchange_type}` staff role set to {role.mention}"
    )


@bot.command(name="I2C")
@is_admin()
async def i2c(ctx, role: discord.Role):
    await set_role(ctx, "I2C", role)


@bot.command(name="C2I")
@is_admin()
async def c2i(ctx, role: discord.Role):
    await set_role(ctx, "C2I", role)


@bot.command(name="C2C")
@is_admin()
async def c2c(ctx, role: discord.Role):
    await set_role(ctx, "C2C", role)


@bot.command(name="N2C")
@is_admin()
async def n2c(ctx, role: discord.Role):
    await set_role(ctx, "N2C", role)


@bot.command(name="C2N")
@is_admin()
async def c2n(ctx, role: discord.Role):
    await set_role(ctx, "C2N", role)


@bot.command(name="B2C")
@is_admin()
async def b2c(ctx, role: discord.Role):
    await set_role(ctx, "B2C", role)


@bot.command(name="C2B")
@is_admin()
async def c2b(ctx, role: discord.Role):
    await set_role(ctx, "C2B", role)


# =========================================================
# DEAL
# =========================================================

@bot.command()
async def deal(ctx):

    ticket = database.get_ticket(
        ctx.channel.id
    )

    if not ticket:

        await ctx.send(
            "❌ This isn't a Winter Exchange ticket."
        )
        return

    role_id = database.get_setting(
        f"role_{ticket[4]}"
    )

    if role_id:

        role = ctx.guild.get_role(
            int(role_id)
        )

        if role and role not in ctx.author.roles:

            await ctx.send(
                "❌ You don't have the required exchanger role."
            )
            return

    if ticket[10]:

        await ctx.send(
            "❌ This ticket is already claimed."
        )
        return

    database.claim_ticket(
        ctx.channel.id,
        ctx.author.id
    )

    await ctx.send(
        f"🔒 Ticket claimed by {ctx.author.mention}"
    )


# =========================================================
# DONE
# =========================================================

@bot.command()
async def done(ctx):

    ticket = database.get_ticket(
        ctx.channel.id
    )

    if not ticket:

        await ctx.send(
            "❌ This isn't a Winter Exchange ticket."
        )
        return

    if ticket[10] != ctx.author.id:

        await ctx.send(
            "❌ Only the exchanger who claimed this "
            "ticket can use `.done`."
        )
        return

    database.close_ticket(
        ctx.channel.id
    )

    await ctx.send(
        "✅ Exchange completed. Ticket closed."
    )


# =========================================================
# DELETE
# =========================================================

@bot.command()
@is_admin()
async def delete(ctx):

    ticket = database.get_ticket(
        ctx.channel.id
    )

    if not ticket:

        await ctx.send(
            "❌ This isn't a Winter Exchange ticket."
        )
        return

    await ctx.send(
        "🗑️ Deleting ticket..."
    )

    await ctx.channel.delete(
        reason=f"Deleted by {ctx.author}"
    )


# =========================================================
# REOPEN
# =========================================================

@bot.command()
@is_admin()
async def reopen(ctx):

    ticket = database.get_ticket(
        ctx.channel.id
    )

    if not ticket:

        await ctx.send(
            "❌ This isn't a Winter Exchange ticket."
        )
        return

    database.reopen_ticket(
        ctx.channel.id
    )

    await ctx.send(
        "🔓 Ticket reopened."
    )


# =========================================================
# ERROR HANDLER
# =========================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.CheckFailure):

        await ctx.send(
            "❌ You need Administrator permission "
            "to use this command.",
            delete_after=5
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):

        await ctx.send(
            "❌ Missing argument.\n"
            "Example: `.exchpanel #channel`",
            delete_after=5
        )
        return

    if isinstance(error, commands.BadArgument):

        await ctx.send(
            "❌ Invalid channel or role.\n"
            "Please mention it correctly.",
            delete_after=5
        )
        return

    print(f"[ERROR] {type(error).__name__}: {error}")


# =========================================================
# START BOT
# =========================================================

if not TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is missing from your .env file."
    )

print("Starting Winter Exchange...")

bot.run(TOKEN)
