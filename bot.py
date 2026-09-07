import os
import discord

from discord.ext import commands
from discord.ui import View, Select, Button

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

        if not ctx.guild:
            return False

        return ctx.author.guild_permissions.administrator

    return commands.check(predicate)


# =========================================================
# EXCHANGE TYPE
# =========================================================

def get_exchange_type(source, receiving):

    if source == "INR":
        return "I2C"

    if source == "NPR":
        return "N2C"

    if source == "BDT":
        return "B2C"

    if source == "CRYPTO":

        if receiving == "INR":
            return "C2I"

        if receiving == "NPR":
            return "C2N"

        if receiving == "BDT":
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
# RATE BUTTON
# =========================================================

class RateButton(Button):

    def __init__(self):

        super().__init__(
            label="Rates",
            style=discord.ButtonStyle.secondary
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


# =========================================================
# CREATE TICKET BUTTON
# =========================================================

class CreateTicketButton(Button):

    def __init__(self):

        super().__init__(
            label="Create Ticket",
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction):

        await interaction.response.send_message(
            "### Currently you are Sending",
            view=CurrencyView(),
            ephemeral=True
        )


# =========================================================
# PANEL VIEW
# =========================================================

class PanelView(View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(CreateTicketButton())
        self.add_item(RateButton())


# =========================================================
# CURRENCY SELECT
# =========================================================

class CurrencySelect(Select):

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
                view=CryptoSendingView(source)
            )

        else:

            await interaction.response.edit_message(
                content="### Choose the app for Money Transfer",
                view=PaymentView(source)
            )


class CurrencyView(View):

    def __init__(self):

        super().__init__(timeout=300)

        self.add_item(CurrencySelect())


# =========================================================
# PAYMENT SELECT
# =========================================================

class PaymentSelect(Select):

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


class PaymentView(View):

    def __init__(self, source):

        super().__init__(timeout=300)

        self.add_item(PaymentSelect(source))


# =========================================================
# CRYPTO SENDING
# =========================================================

class SendingCryptoSelect(Select):

    def __init__(self, source):

        self.source = source

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
                self.source,
                None,
                crypto
            )
        )


class CryptoSendingView(View):

    def __init__(self, source):

        super().__init__(timeout=300)

        self.add_item(
            SendingCryptoSelect(source)
        )


# =========================================================
# RECEIVING CRYPTO
# =========================================================

class ReceivingCryptoSelect(Select):

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
                "Use the keypad below to enter the amount."
            ),
            view=KeypadView(
                self.source,
                self.payment,
                self.sending_crypto,
                receiving_crypto
            )
        )


class ReceivingCryptoView(View):

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

class KeypadView(View):

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

        for number in ["1", "2", "3",
                       "4", "5", "6",
                       "7", "8", "9",
                       ".", "0"]:

            button = Button(
                label=number,
                style=discord.ButtonStyle.secondary
            )

            button.callback = self.number_callback(number)

            self.add_item(button)

        delete = Button(
            label="⌫",
            style=discord.ButtonStyle.danger
        )

        delete.callback = self.delete_callback

        self.add_item(delete)

        confirm = Button(
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

        exchange_type = get_exchange_type(
            self.source,
            "CRYPTO" if self.source != "CRYPTO"
            else self.receiving_crypto
        )

        await interaction.response.edit_message(
            content="⏳ Creating your ticket...",
            view=None
        )

        await create_ticket(
            interaction,
            exchange_type,
            self.source,
            self.payment,
            self.sending_crypto,
            self.receiving_crypto,
            amount
        )


# =========================================================
# GET STAFF ROLE
# =========================================================

def get_role_id(exchange_type):

    return database.get_setting(
        f"role_{exchange_type}"
    )


# =========================================================
# CREATE TICKET
# =========================================================

async def create_ticket(
    interaction,
    exchange_type,
    source,
    payment,
    sending_crypto,
    receiving_crypto,
    amount
):

    guild = interaction.guild

    number = database.get_setting("ticket_counter")

    if number is None:
        number = 1
    else:
        number = int(number) + 1

    database.set_setting(
        "ticket_counter",
        number
    )

    role_id = get_role_id(exchange_type)

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

    category = None

    for cat in guild.categories:

        if cat.name.lower() == "winter tickets":

            category = cat
            break

    if category is None:

        category = await guild.create_category(
            "Winter Tickets"
        )

    channel_name = (
        f"{exchange_type.lower()}-{number:03d}"
    )

    channel = await guild.create_text_channel(
        channel_name,
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

    embed = discord.Embed(
        title="Exchange Summary",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="Deal Amount",
        value=f"{amount} {source}",
        inline=False
    )

    if payment:
        embed.add_field(
            name="Payment App",
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
        name="User Receiving",
        value=f"Crypto ({receiving_crypto})",
        inline=False
    )

    embed.add_field(
        name="Type",
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
# TICKET VIEW
# =========================================================

class DealButton(Button):

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
                "❌ This is not a Winter Exchange ticket.",
                ephemeral=True
            )

            return

        exchange_type = ticket[4]

        role_id = get_role_id(exchange_type)

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

        try:

            await interaction.channel.edit(
                name=(
                    f"{exchange_type.lower()}-"
                    f"{ticket[2]:03d}-"
                    f"{interaction.user.name.lower()[:15]}"
                )
            )

        except:
            pass

        await interaction.response.send_message(
            f"✅ Ticket claimed by {interaction.user.mention}.",
        )


class DoneButton(Button):

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
                "❌ Not a ticket.",
                ephemeral=True
            )

            return

        claimed = ticket[10]

        if not claimed:

            await interaction.response.send_message(
                "❌ This ticket has not been claimed.",
                ephemeral=True
            )

            return

        if claimed != interaction.user.id:

            await interaction.response.send_message(
                "❌ Only the exchanger who claimed this ticket "
                "can complete it.",
                ephemeral=True
            )

            return

        database.close_ticket(
            interaction.channel.id
        )

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            view_channel=False
        )

        user = interaction.guild.get_member(
            ticket[3]
        )

        if user:

            await interaction.channel.set_permissions(
                user,
                view_channel=False
            )

        await send_log(
            interaction.guild,
            interaction.channel,
            ticket,
            interaction.user
        )

        await interaction.response.send_message(
            "✅ Exchange completed. Ticket closed."
        )


class CloseButton(Button):

    def __init__(self):

        super().__init__(
            label="Close Ticket",
            style=discord.ButtonStyle.danger
        )

    async def callback(self, interaction):

        await interaction.response.send_message(
            "Use `.done` after completing the exchange."
        )


class TicketView(View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(DealButton())
        self.add_item(DoneButton())
        self.add_item(CloseButton())


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
        return

    log_channel = guild.get_channel(
        int(log_channel_id)
    )

    if not log_channel:
        return

    # Logging implementation placeholder — add detailed logging here.
    try:
        await log_channel.send(
            f"Ticket #{ticket[2]:03d} closed by {exchanger.mention}"
        )
    except Exception:
        # Fail silently to avoid crashing the bot on logging errors
        pass


# If you want the bot to start when this file is run directly, uncomment below
# bot.run(TOKEN)
