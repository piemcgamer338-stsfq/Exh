import os
import asyncio
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
# CALCULATE EXCHANGE
# =========================================================

def calculate_exchange(
    exchange_type,
    amount
):

    if exchange_type == "I2C":

        usd = amount / 104

        return (
            f"₹{amount:g}",
            f"${usd:.2f}"
        )

    elif exchange_type == "C2I":

        inr = amount * 100

        return (
            f"${amount:g}",
            f"₹{inr:.2f}"
        )

    elif exchange_type == "C2C":

        received = amount * 0.95

        return (
            f"${amount:g}",
            f"${received:.2f}"
        )

    elif exchange_type == "N2C":

        usd = amount / 165

        return (
            f"रू{amount:g}",
            f"${usd:.2f}"
        )

    elif exchange_type == "C2N":

        npr = amount * 150

        return (
            f"${amount:g}",
            f"रू{npr:.2f}"
        )

    elif exchange_type == "B2C":

        usd = amount / 142

        return (
            f"৳{amount:g}",
            f"${usd:.2f}"
        )

    elif exchange_type == "C2B":

        bdt = amount * 118

        return (
            f"${amount:g}",
            f"৳{bdt:.2f}"
        )

    return (
        str(amount),
        "Unknown"
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

        super().__init__(
            timeout=None
        )

        self.add_item(
            CreateTicketButton()
        )

        self.add_item(
            RateButton()
        )


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

        super().__init__(
            timeout=300
        )

        self.add_item(
            CurrencySelect()
        )


# =========================================================
# PAYMENT SELECT
# =========================================================

class PaymentSelect(Select):

    def __init__(self, source):

        self.source = source

        options = [
            discord.SelectOption(
                label=x
            )
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

        super().__init__(
            timeout=300
        )

        self.add_item(
            PaymentSelect(source)
        )


# =========================================================
# SENDING CRYPTO
# =========================================================

class SendingCryptoSelect(Select):

    def __init__(self, source):

        self.source = source

        options = [
            discord.SelectOption(
                label=x
            )
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

        super().__init__(
            timeout=300
        )

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
            discord.SelectOption(
                label=x
            )
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

        super().__init__(
            timeout=300
        )

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

        super().__init__(
            timeout=300
        )

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

            button = Button(
                label=number,
                style=discord.ButtonStyle.secondary
            )

            button.callback = self.number_callback(
                number
            )

            self.add_item(button)

        delete = Button(
            label="⌫",
            style=discord.ButtonStyle.danger
        )

        delete.callback = self.delete_callback

        self.add_item(delete)

        confirm = Button(
            label="Confirm",
            style=discord.ButtonStyle.success
        )

        confirm.callback = self.confirm_callback

        self.add_item(confirm)

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

                    await interaction.response.send_message(
                        "❌ You can only use one decimal point.",
                        ephemeral=True
                    )

                    return

                if not self.amount:

                    self.amount = "0"

            self.amount += number

            await interaction.response.edit_message(
                content=(
                    "### Enter your amount\n\n"
                    f"**Amount:** `{self.amount or '0'}`"
                ),
                view=self
            )

        return callback

    async def delete_callback(
        self,
        interaction
    ):

        self.amount = self.amount[:-1]

        await interaction.response.edit_message(
            content=(
                "### Enter your amount\n\n"
                f"**Amount:** `{self.amount or '0'}`"
            ),
            view=self
        )

    async def confirm_callback(
        self,
        interaction
    ):

        if not self.amount:

            await interaction.response.send_message(
                "❌ Please enter an amount.",
                ephemeral=True
            )

            return

        try:

            amount = float(
                self.amount
            )

            if amount <= 0:
                raise ValueError

        except ValueError:

            await interaction.response.send_message(
                "❌ Invalid amount.",
                ephemeral=True
            )

            return

        if self.source == "CRYPTO":

            exchange_type = get_exchange_type(
                self.source,
                self.receiving_crypto
            )

        else:

            exchange_type = get_exchange_type(
                self.source,
                "CRYPTO"
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

    number = database.get_setting(
        "ticket_counter"
    )

    if number is None:

        number = 1

    else:

        number = int(number) + 1

    database.set_setting(
        "ticket_counter",
        number
    )

    role_id = get_role_id(
        exchange_type
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

    from_text, to_text = calculate_exchange(
        exchange_type,
        amount
    )

    embed = discord.Embed(
        title="Exchange Summary",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="From",
        value=from_text,
        inline=False
    )

    embed.add_field(
        name="Receiving",
        value=to_text,
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

    if receiving_crypto:

        embed.add_field(
            name="Receiving Crypto",
            value=receiving_crypto,
            inline=False
        )

    embed.add_field(
        name="Exchange Type",
        value=exchange_type,
        inline=False
    )

    embed.set_footer(
        text=(
            f"Winter Exchange • "
            f"Ticket #{number:03d}"
        )
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
        content=(
            f"✅ Ticket created: "
            f"{channel.mention}"
        ),
        view=None
    )


# =========================================================
# CLAIM BUTTON
# =========================================================

class ClaimButton(Button):

    def __init__(self):

        super().__init__(
            label="Claim Ticket",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction
    ):

        ticket = database.get_ticket(
            interaction.channel.id
        )

        if not ticket:

            await interaction.response.send_message(
                "❌ This isn't a Winter Exchange ticket.",
                ephemeral=True
            )

            return

        if ticket[11]:

            await interaction.response.send_message(
                "❌ This ticket is already closed.",
                ephemeral=True
            )

            return

        role_id = get_role_id(
            ticket[4]
        )

        if role_id:

            role = interaction.guild.get_role(
                int(role_id)
            )

            if role and role not in interaction.user.roles:

                await interaction.response.send_message(
                    "❌ You don't have the required "
                    "exchanger role.",
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
                    f"{ticket[4].lower()}-"
                    f"{ticket[2]:03d}-"
                    f"{interaction.user.name.lower()[:15]}"
                )
            )

        except Exception as e:

            print(
                f"[RENAME ERROR] {e}"
            )

        await interaction.response.send_message(
            f"🔒 **Ticket Claimed**\n"
            f"Exchanger: {interaction.user.mention}"
        )


# =========================================================
# DONE BUTTON
# =========================================================

class DoneButton(Button):

    def __init__(self):

        super().__init__(
            label="Done",
            style=discord.ButtonStyle.success
        )

    async def callback(
        self,
        interaction
    ):

        ticket = database.get_ticket(
            interaction.channel.id
        )

        if not ticket:

            await interaction.response.send_message(
                "❌ This isn't a Winter Exchange ticket.",
                ephemeral=True
            )

            return

        if ticket[11]:

            await interaction.response.send_message(
                "❌ This ticket is already closed.",
                ephemeral=True
            )

            return

        claimed = ticket[10]

        if not claimed:

            await interaction.response.send_message(
                "❌ This ticket hasn't been claimed.",
                ephemeral=True
            )

            return

        if claimed != interaction.user.id:

            await interaction.response.send_message(
                "❌ Only the exchanger who claimed "
                "this ticket can use Done.",
                ephemeral=True
            )

            return

        customer = interaction.guild.get_member(
            ticket[3]
        )

        if not customer:

            await interaction.response.send_message(
                "❌ Customer could not be found.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="Exchange Confirmation",
            description=(
                f"Hey {customer.mention}!\n\n"
                "**The Exchange has been Done?**\n\n"
                "Just for a small confirmation after "
                "receiving payment click on "
                "**Yes, Received**."
            ),
            color=discord.Color.green()
        )

        await interaction.response.send_message(
            content=customer.mention,
            embed=embed,
            view=ReceivedView(
                customer.id
            )
        )


# =========================================================
# YES RECEIVED BUTTON
# =========================================================

class ReceivedButton(Button):

    def __init__(
        self,
        customer_id
    ):

        self.customer_id = customer_id

        super().__init__(
            label="Yes, Received",
            style=discord.ButtonStyle.success
        )

    async def callback(
        self,
        interaction
    ):

        if interaction.user.id != self.customer_id:

            await interaction.response.send_message(
                "❌ Only the person who opened "
                "this ticket can confirm the payment.",
                ephemeral=True
            )

            return

        ticket = database.get_ticket(
            interaction.channel.id
        )

        if not ticket:

            await interaction.response.send_message(
                "❌ Ticket information could not be found.",
                ephemeral=True
            )

            return

        if ticket[11]:

            await interaction.response.send_message(
                "❌ This ticket is already closed.",
                ephemeral=True
            )

            return

        exchanger_id = ticket[10]

        if not exchanger_id:

            await interaction.response.send_message(
                "❌ No exchanger is assigned to this ticket.",
                ephemeral=True
            )

            return

        amount = float(
            ticket[9]
        )

        from_text, to_text = calculate_exchange(
            ticket[4],
            amount
        )

        exchanger = interaction.guild.get_member(
            int(exchanger_id)
        )

        if exchanger:

            exchanger_name = exchanger.name

        else:

            exchanger_name = "Unknown"

        # =================================================
        # FINAL CONFIRMATION
        # =================================================

        embed = discord.Embed(
            title="✅ Exchange Confirmed",
            description=(
                f"Thank you {interaction.user.mention}!\n\n"
                "Your exchange has been confirmed as received."
            ),
            color=discord.Color.green()
        )

        embed.add_field(
            name="Rate Your Experience",
            value=(
                "[Click Here](https://discord.com/channels/"
                "1536684234352230480/"
                "1546181630497001502)"
            ),
            inline=False
        )

        embed.add_field(
            name="Voucher the Exchanger",
            value=(
                "[Click Here](https://discord.com/channels/"
                "1536684234352230480/"
                "1546181637459542097)"
            ),
            inline=False
        )

        # Correct rep amount based on amount received
        if ticket[4] in [
            "I2C",
            "N2C",
            "B2C"
        ]:

            rep_amount = (
                float(
                    to_text.replace(
                        "$",
                        ""
                    )
                )
            )

        elif ticket[4] == "C2C":

            rep_amount = (
                float(
                    to_text.replace(
                        "$",
                        ""
                    )
                )
            )

        else:

            rep_amount = amount

        rep_text = (
            f"+rep {exchanger_id} "
            f"{rep_amount:.2f}$ "
            f"{ticket[7] or 'USDT'} to UPI"
        )

        embed.add_field(
            name="Rep",
            value=f"`{rep_text}`",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )

        # =================================================
        # LOG
        # =================================================

        await send_log(
            interaction.guild,
            interaction.channel,
            ticket,
            exchanger_id
        )

        # =================================================
        # CLOSE DATABASE
        # =================================================

        database.close_ticket(
            interaction.channel.id
        )

        # =================================================
        # CLOSE CHANNEL
        # =================================================

        try:

            await interaction.channel.set_permissions(
                interaction.guild.default_role,
                view_channel=False
            )

            await interaction.channel.set_permissions(
                interaction.user,
                view_channel=False
            )

        except Exception as e:

            print(
                f"[CLOSE PERMISSION ERROR] {e}"
            )

        try:

            await interaction.channel.send(
                "🔒 **Ticket closed.**\n"
                "The exchange has been completed."
            )

        except Exception:

            pass


# =========================================================
# RECEIVED VIEW
# =========================================================

class ReceivedView(View):

    def __init__(
        self,
        customer_id
    ):

        super().__init__(
            timeout=None
        )

        self.add_item(
            ReceivedButton(
                customer_id
            )
        )


# =========================================================
# TICKET VIEW
# =========================================================

class TicketView(View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            ClaimButton()
        )

        self.add_item(
            DoneButton()
        )


# =========================================================
# SEND LOG
# =========================================================

async def send_log(
    guild,
    channel,
    ticket,
    exchanger_id
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

    except (
        ValueError,
        TypeError
    ):

        print(
            "[LOG] Invalid log channel ID."
        )

        return

    if not log_channel:

        print(
            "[LOG] Log channel not found."
        )

        return

    exchanger = guild.get_member(
        int(exchanger_id)
    )

    customer = guild.get_member(
        int(ticket[3])
    )

    amount = float(
        ticket[9]
    )

    from_text, to_text = calculate_exchange(
        ticket[4],
        amount
    )

    if exchanger:

        exchanger_name = exchanger.name
        exchanger_mention = exchanger.mention

    else:

        exchanger_name = "Unknown"
        exchanger_mention = f"<@{exchanger_id}>"

    if customer:

        customer_text = customer.mention

    else:

        customer_text = f"<@{ticket[3]}>"

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
            f"- {exchanger_mention}, "
            f"{exchanger_name}\n"
            f"- ID: {exchanger_id}"
        ),
        inline=False
    )

    embed.add_field(
        name="Customer:",
        value=(
            f"- {customer_text}\n"
            f"- ID: {ticket[3]}"
        ),
        inline=False
    )

    if ticket[6]:

        embed.add_field(
            name="Payment Method:",
            value=ticket[6],
            inline=False
        )

    if ticket[7]:

        embed.add_field(
            name="Sending Crypto:",
            value=ticket[7],
            inline=False
        )

    if ticket[8]:

        embed.add_field(
            name="Receiving Crypto:",
            value=ticket[8],
            inline=False
        )

    embed.add_field(
        name="Exchange Type:",
        value=ticket[4],
        inline=False
    )

    embed.add_field(
        name="Ticket:",
        value=channel.mention,
        inline=False
    )

    embed.set_footer(
        text=(
            f"Winter Exchange • "
            f"Ticket #{ticket[2]:03d}"
        )
    )

    try:

        await log_channel.send(
            embed=embed
        )

        print(
            f"[LOG] Ticket #{ticket[2]:03d} logged."
        )

    except Exception as e:

        print(
            f"[LOG ERROR] "
            f"{type(e).__name__}: {e}"
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
            "**Ticket Commands**\n"
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
# EXCHANGE PANEL
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
# EXCHANGE LOG CHANNEL
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
        f"[LOG SETUP] "
        f"{channel.name} ({channel.id})"
    )

# =========================================================
# SET STAFF ROLE
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
async def i2c(
    ctx,
    role: discord.Role
):

    await set_role(
        ctx,
        "I2C",
        role
    )


@bot.command(name="C2I")
@is_admin()
async def c2i(
    ctx,
    role: discord.Role
):

    await set_role(
        ctx,
        "C2I",
        role
    )


@bot.command(name="C2C")
@is_admin()
async def c2c(
    ctx,
    role: discord.Role
):

    await set_role(
        ctx,
        "C2C",
        role
    )


@bot.command(name="N2C")
@is_admin()
async def n2c(
    ctx,
    role: discord.Role
):

    await set_role(
        ctx,
        "N2C",
        role
    )


@bot.command(name="C2N")
@is_admin()
async def c2n(
    ctx,
    role: discord.Role
):

    await set_role(
        ctx,
        "C2N",
        role
    )


@bot.command(name="B2C")
@is_admin()
async def b2c(
    ctx,
    role: discord.Role
):

    await set_role(
        ctx,
        "B2C",
        role
    )


@bot.command(name="C2B")
@is_admin()
async def c2b(
    ctx,
    role: discord.Role
):

    await set_role(
        ctx,
        "C2B",
        role
    )


# =========================================================
# DEAL COMMAND
# =========================================================

@bot.command(name="deal")
async def deal(ctx):

    ticket = database.get_ticket(
        ctx.channel.id
    )

    if not ticket:

        await ctx.send(
            "❌ This isn't a Winter Exchange ticket."
        )

        return

    if ticket[11]:

        await ctx.send(
            "❌ This ticket is already closed."
        )

        return

    role_id = get_role_id(
        ticket[4]
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

    try:

        await ctx.channel.edit(
            name=(
                f"{ticket[4].lower()}-"
                f"{ticket[2]:03d}-"
                f"{ctx.author.name.lower()[:15]}"
            )
        )

    except Exception as e:

        print(
            f"[RENAME ERROR] {e}"
        )

    await ctx.send(
        f"🔒 **Ticket Claimed**\n"
        f"Exchanger: {ctx.author.mention}"
    )


# =========================================================
# DONE COMMAND
# =========================================================

@bot.command(name="done")
async def done(ctx):

    ticket = database.get_ticket(
        ctx.channel.id
    )

    if not ticket:

        await ctx.send(
            "❌ This isn't a Winter Exchange ticket."
        )

        return

    if ticket[11]:

        await ctx.send(
            "❌ This ticket is already closed."
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

    customer = ctx.guild.get_member(
        ticket[3]
    )

    if not customer:

        await ctx.send(
            "❌ The customer could not be found."
        )

        return

    embed = discord.Embed(
        title="Exchange Confirmation",
        description=(
            f"Hey {customer.mention}!\n\n"
            "**The Exchange has been Done?**\n\n"
            "Just for a small confirmation after "
            "receiving payment click on "
            "**Yes, Received**."
        ),
        color=discord.Color.green()
    )

    await ctx.send(
        content=customer.mention,
        embed=embed,
        view=ReceivedView(
            customer.id
        )
    )


# =========================================================
# DELETE COMMAND
# =========================================================

@bot.command(name="delete")
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

    await asyncio.sleep(2)

    try:

        await ctx.channel.delete(
            reason=(
                f"Deleted by {ctx.author}"
            )
        )

    except Exception as e:

        print(
            f"[DELETE ERROR] {e}"
        )


# =========================================================
# REOPEN COMMAND
# =========================================================

@bot.command(name="reopen")
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

    customer = ctx.guild.get_member(
        ticket[3]
    )

    if customer:

        await ctx.channel.set_permissions(
            customer,
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )

    role_id = get_role_id(
        ticket[4]
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

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        view_channel=False
    )

    await ctx.send(
        "🔓 **Ticket Reopened**\n"
        "The ticket is now open again."
    )


# =========================================================
# COMMAND ERROR HANDLER
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
            "❌ You need Administrator permissions "
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
            delete_after=7
        )

        return

    if isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ Invalid argument.\n"
            "Please mention the correct channel or role.",
            delete_after=7
        )

        return

    print(
        f"[COMMAND ERROR] "
        f"{type(error).__name__}: {error}"
    )


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    print("=" * 55)
    print("❄️ WINTER EXCHANGE")
    print("=" * 55)

    print(
        f"✅ Logged in as: "
        f"{bot.user} "
        f"(ID: {bot.user.id})"
    )

    print(
        f"📡 Servers: {len(bot.guilds)}"
    )

    print(
        f"⚙️ Prefix: {PREFIX}"
    )

    print(
        "🚀 Bot is ready!"
    )

    print("=" * 55)

    try:

        await bot.change_presence(
            activity=discord.Game(
                name=".help | Winter Exchange"
            )
        )

    except Exception as e:

        print(
            f"[PRESENCE ERROR] {e}"
        )


# =========================================================
# START BOT
# =========================================================

if not TOKEN:

    print(
        "❌ ERROR: BOT_TOKEN was not found "
        "in your .env file."
    )

else:

    print(
        "🚀 Starting Winter Exchange..."
    )

    bot.run(TOKEN)