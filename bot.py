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
# RATE CALCULATOR
# =========================================================

def get_rate_number(rate):

    """
    Converts values such as:
        '104/$'
        '₹104/$'
        '165/$'
        '5% Fees'

    into a number.
    """

    if isinstance(rate, (int, float)):
        return float(rate)

    text = str(rate)

    if "%" in text:
        return None

    cleaned = ""

    for char in text:

        if char.isdigit() or char == ".":

            cleaned += char

    if not cleaned:
        return None

    return float(cleaned)


def calculate_exchange(
    exchange_type,
    amount
):

    """
    Returns:
        from_text,
        to_text
    """

    if exchange_type == "I2C":

        rate = get_rate_number(RATES["I2C"])
        result = amount / rate

        return (
            f"₹{amount:,.2f}",
            f"${result:,.2f}"
        )

    if exchange_type == "C2I":

        rate = get_rate_number(RATES["C2I"])
        result = amount * rate

        return (
            f"${amount:,.2f}",
            f"₹{result:,.2f}"
        )

    if exchange_type == "N2C":

        rate = get_rate_number(RATES["N2C"])
        result = amount / rate

        return (
            f"₨{amount:,.2f}",
            f"${result:,.2f}"
        )

    if exchange_type == "C2N":

        rate = get_rate_number(RATES["C2N"])
        result = amount * rate

        return (
            f"${amount:,.2f}",
            f"₨{result:,.2f}"
        )

    if exchange_type == "B2C":

        rate = get_rate_number(RATES["B2C"])
        result = amount / rate

        return (
            f"৳{amount:,.2f}",
            f"${result:,.2f}"
        )

    if exchange_type == "C2B":

        rate = get_rate_number(RATES["C2B"])
        result = amount * rate

        return (
            f"${amount:,.2f}",
            f"৳{result:,.2f}"
        )

    if exchange_type == "C2C":

        # 5% exchange fee
        result = amount * 0.95

        return (
            f"${amount:,.2f}",
            f"${result:,.2f} after 5% fee"
        )

    return (
        str(amount),
        "Unknown"
    )


# =========================================================
# EXCHANGE TYPE
# =========================================================

def get_exchange_type(
    source,
    receiving_currency=None
):

    if source == "INR":
        return "I2C"

    if source == "NPR":
        return "N2C"

    if source == "BDT":
        return "B2C"

    if source == "CRYPTO":

        if receiving_currency == "INR":
            return "C2I"

        if receiving_currency == "NPR":
            return "C2N"

        if receiving_currency == "BDT":
            return "C2B"

        return "C2C"

    return "UNKNOWN"


# =========================================================
# RATE TEXT
# =========================================================

def rate_text():

    return (
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


# =========================================================
# PANEL BUTTONS
# =========================================================

class RateButton(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Rates",
            style=discord.ButtonStyle.secondary,
            custom_id="winter_rates"
        )

    async def callback(self, interaction):

        embed = discord.Embed(
            title="Winter Exchange Rates",
            description=rate_text(),
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
# CURRENCY SELECT
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
            options=options
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
# PAYMENT SELECT
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

        self.add_item(
            PaymentSelect(source)
        )


# =========================================================
# SENDING CRYPTO
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

        self.add_item(
            SendingCryptoSelect()
        )


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
                "### Enter the amount\n\n"
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
# AMOUNT KEYBOARD
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

        # Row 0
        self.add_number("1", 0)
        self.add_number("2", 0)
        self.add_number("3", 0)

        # Row 1
        self.add_number("4", 1)
        self.add_number("5", 1)
        self.add_number("6", 1)

        # Row 2
        self.add_number("7", 2)
        self.add_number("8", 2)
        self.add_number("9", 2)

        # Row 3
        self.add_number(".", 3)
        self.add_number("0", 3)

        back = discord.ui.Button(
            label="⌫",
            style=discord.ButtonStyle.danger,
            row=3
        )

        back.callback = self.backspace
        self.add_item(back)

        # Row 4
        clear = discord.ui.Button(
            label="Clear",
            style=discord.ButtonStyle.danger,
            row=4
        )

        clear.callback = self.clear
        self.add_item(clear)

        confirm = discord.ui.Button(
            label="Confirm",
            style=discord.ButtonStyle.success,
            row=4
        )

        confirm.callback = self.confirm
        self.add_item(confirm)

    def add_number(self, number, row):

        button = discord.ui.Button(
            label=number,
            style=discord.ButtonStyle.secondary,
            row=row
        )

        button.callback = self.number_callback(number)

        self.add_item(button)

    def display(self):

        if not self.amount:
            return "0"

        return self.amount

    def number_callback(self, number):

        async def callback(interaction):

            if len(self.amount) >= 15:

                await interaction.response.send_message(
                    "❌ Maximum amount length reached.",
                    ephemeral=True
                )
                return

            if number == ".":

                if "." in self.amount:
                    await interaction.response.defer()
                    return

                if not self.amount:
                    self.amount = "0"

            self.amount += number

            await interaction.response.edit_message(
                content=(
                    "### Enter the amount\n\n"
                    f"**Amount:** `{self.display()}`"
                ),
                view=self
            )

        return callback

    async def backspace(self, interaction):

        self.amount = self.amount[:-1]

        await interaction.response.edit_message(
            content=(
                "### Enter the amount\n\n"
                f"**Amount:** `{self.display()}`"
            ),
            view=self
        )

    async def clear(self, interaction):

        self.amount = ""

        await interaction.response.edit_message(
            content=(
                "### Enter the amount\n\n"
                "**Amount:** `0`"
            ),
            view=self
        )

    async def confirm(self, interaction):

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

    exchange_type = get_exchange_type(
        source,
        receiving_crypto
    )

    counter = database.get_setting(
        "ticket_counter"
    )

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

        role = guild.get_role(
            int(role_id)
        )

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
        overwrites=overwrites,
        reason="Winter Exchange ticket"
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

    # Calculate From -> To
    from_text, to_text = calculate_exchange(
        exchange_type,
        amount
    )

    # =====================================================
    # FIRST EMBED
    # =====================================================

    embed = discord.Embed(
        title="Exchange Details",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="From:",
        value=from_text,
        inline=False
    )

    embed.add_field(
        name="To:",
        value=to_text,
        inline=False
    )

    embed.add_field(
        name="Customer:",
        value=interaction.user.mention,
        inline=False
    )

    if payment:

        embed.add_field(
            name="Payment Method:",
            value=payment,
            inline=False
        )

    if sending_crypto:

        embed.add_field(
            name="Sending Crypto:",
            value=sending_crypto,
            inline=False
        )

    embed.add_field(
        name="Receiving Crypto:",
        value=receiving_crypto,
        inline=False
    )

    embed.add_field(
        name="Exchange Type:",
        value=exchange_type,
        inline=False
    )

    embed.set_footer(
        text=f"Winter Exchange • Ticket #{number:03d}"
    )

    await channel.send(
        content=interaction.user.mention,
        embed=embed
    )

    # =====================================================
    # SAFETY EMBED
    # =====================================================

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

        # Send the log BEFORE hiding the ticket
        await send_log(
            interaction.guild,
            interaction.channel,
            ticket,
            interaction.user
        )

        await interaction.response.send_message(
            "✅ Exchange completed. Ticket closed."
        )

        # Hide customer
        user = interaction.guild.get_member(
            ticket[3]
        )

        if user:

            try:

                await interaction.channel.set_permissions(
                    user,
                    view_channel=False
                )

            except Exception as e:

                print(
                    f"[PERMISSION ERROR] {e}"
                )


class TicketView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(ClaimButton())
        self.add_item(DoneButton())


# =========================================================
# LOGGING
# =========================================================

async def send_log(
    guild,
    channel,
    ticket,
    exchanger
):

    log_channel_id = database.get_setting(
        "log_channel"
    )

    if not log_channel_id:

        print(
            "[LOG] No log channel configured."
        )

        return

    try:

        log_channel = guild.get_channel(
            int(log_channel_id)
        )

    except (ValueError, TypeError):

        print(
            "[LOG] Invalid log channel ID."
        )

        return

    if log_channel is None:

        print(
            "[LOG] Log channel was not found."
        )

        return

    exchange_type = ticket[4]
    amount = float(ticket[8])

    from_text, to_text = calculate_exchange(
        exchange_type,
        amount
    )

    user = guild.get_member(
        ticket[3]
    )

    user_text = (
        f"{user.mention}\nID: {ticket[3]}"
        if user
        else f"ID: {ticket[3]}"
    )

    embed = discord.Embed(
        title="Exchange Details",
        color=discord.Color.green()
    )

    embed.add_field(
        name="From:",
        value=from_text,
        inline=False
    )

    embed.add_field(
        name="To:",
        value=to_text,
        inline=False
    )

    embed.add_field(
        name="Exchanger:",
        value=(
            f"- {exchanger.mention}, {exchanger.name}\n"
            f"- ID: {exchanger.id}"
        ),
        inline=False
    )

    embed.add_field(
        name="Customer:",
        value=user_text,
        inline=False
    )

    if ticket[5]:

        embed.add_field(
            name="Payment Method:",
            value=ticket[5],
            inline=False
        )

    if ticket[6]:

        embed.add_field(
            name="Sending Crypto:",
            value=ticket[6],
            inline=False
        )

    embed.add_field(
        name="Receiving Crypto:",
        value=ticket[7],
        inline=False
    )

    embed.add_field(
        name="Exchange Type:",
        value=exchange_type,
        inline=False
    )

    embed.add_field(
        name="Ticket:",
        value=channel.mention,
        inline=False
    )

    embed.set_footer(
        text=f"Winter Exchange • Ticket #{ticket[2]:03d}"
    )

    try:

        await log_channel.send(
            embed=embed
        )

        print(
            f"[LOG] Sent ticket #{ticket[2]:03d} "
            f"to #{log_channel.name}"
        )

    except Exception as e:

        print(
            f"[LOG ERROR] {type(e).__name__}: {e}"
        )


# =========================================================
# HELP
# =========================================================

@bot.command(name="help")
@is_admin()
async def help_command(ctx):

    embed = discord.Embed(
        title="❄️ Winter Exchange",
        description=(
            "**Ticket System**\n"
            "`.exchpanel #channel`\n"
            "`.exchlog #channel`\n"
            "`.exchlogs #channel`\n"
            "`.deal`\n"
            "`.done`\n"
            "`.delete`\n"
            "`.reopen`\n\n"

            "**Staff Roles**\n"
            "`.I2C @role`\n"
            "`.C2I @role`\n"
            "`.C2C @role`\n"
            "`.N2C @role`\n"
            "`.C2N @role`\n"
            "`.B2C @role`\n"
            "`.C2B @role`"
        ),
        color=discord.Color.blurple()
    )

    await ctx.send(
        embed=embed
    )


# =========================================================
# PANEL COMMAND
# =========================================================

@bot.command()
@is_admin()
async def exchpanel(
    ctx,
    channel: discord.TextChannel
):

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
# LOG COMMAND
# =========================================================

@bot.command(
    name="exchlog",
    aliases=["exchlogs"]
)
@is_admin()
async def exchlog(
    ctx,
    channel: discord.TextChannel
):

    database.set_setting(
        "log_channel",
        channel.id
    )

    await ctx.send(
        f"✅ Exchange logs will now be sent to "
        f"{channel.mention}",
        delete_after=7
    )

    print(
        f"[LOG SETUP] Log channel = "
        f"{channel.name} ({channel.id})"
    )


# =========================================================
# ROLE COMMANDS
# =========================================================

async def set_role(
    ctx,
    exchange_type,
    role
):

    database.set_setting(
        f"role_{exchange_type}",
        role.id
    )

    await ctx.send(
        f"✅ `{exchange_type}` staff role set to "
        f"{role.mention}"
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
                "❌ You don't have the required "
                "exchanger role."
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
# DONE COMMAND
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

    if not ticket[10]:

        await ctx.send(
            "❌ This ticket hasn't been claimed."
        )
        return

    if ticket[10] != ctx.author.id:

        await ctx.send(
            "❌ Only the exchanger who claimed "
            "this ticket can use `.done`."
        )
        return

    database.close_ticket(
        ctx.channel.id
    )

    await send_log(
        ctx.guild,
        ctx.channel,
        ticket,
        ctx.author
    )

    from_text, to_text = calculate_exchange(
        ticket[4],
        float(ticket[8])
    )

    await ctx.send(
        "## ✅ Exchange Completed\n\n"
        "Please Voucher under 30mins\n"
        f"+rep {ctx.author.id} "
        f"{to_text} "
    )

    user = ctx.guild.get_member(
        ticket[3]
    )

    if user:

        try:

            await ctx.channel.set_permissions(
                user,
                view_channel=False
            )

        except Exception as e:

            print(
                f"[PERMISSION ERROR] {e}"
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

    user = ctx.guild.get_member(
        ticket[3]
    )

    if user:

        await ctx.channel.set_permissions(
            user,
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    role_id = database.get_setting(
        f"role_{ticket[4]}"
    )

    if role_id:

        role = ctx.guild.get_role(
            int(role_id)
        )

        if role:

            await ctx.channel.set_permissions(
                role,
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

    await ctx.send(
        "🔓 Ticket reopened."
    )


# =========================================================
# ERROR HANDLER
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    if isinstance(
        error,
        commands.CheckFailure
    ):

        await ctx.send(
            "❌ You need Administrator permission "
            "to use this command.",
            delete_after=5
        )
        return

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Missing argument.\n"
            "Example: `.exchpanel #channel`",
            delete_after=5
        )
        return

    if isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Invalid channel or role.\n"
            "Please mention it correctly.",
            delete_after=5
        )
        return

    print(
        f"[ERROR] {type(error).__name__}: {error}"
    )


# =========================================================
# START
# =========================================================

if not TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is missing from .env"
    )

print("Starting Winter Exchange...")

bot.run(TOKEN)
