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

        if receiving == "CRYPTO":
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

def calculate_exchange(exchange_type, amount):

    if exchange_type == "I2C":

        usd = amount / 104

        return (
            f"₹{amount:g}",
            f"${usd:.2f}"
        )

    if exchange_type == "C2I":

        inr = amount * 100

        return (
            f"${amount:g}",
            f"₹{inr:.2f}"
        )

    if exchange_type == "C2C":

        received = amount * 0.95

        return (
            f"${amount:g}",
            f"${received:.2f}"
        )

    if exchange_type == "N2C":

        usd = amount / 165

        return (
            f"रू{amount:g}",
            f"${usd:.2f}"
        )

    if exchange_type == "C2N":

        npr = amount * 150

        return (
            f"${amount:g}",
            f"रू{npr:.2f}"
        )

    if exchange_type == "B2C":

        usd = amount / 142

        return (
            f"৳{amount:g}",
            f"${usd:.2f}"
        )

    if exchange_type == "C2B":

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
# PANEL BUTTONS
# =========================================================

class CreateTicketButton(Button):

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


class RateButton(Button):

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


class PanelView(View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(CreateTicketButton())
        self.add_item(RateButton())


# =========================================================
# SENDING CURRENCY SELECT
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
                view=SendingCryptoView()
            )

            return

        await interaction.response.edit_message(
            content="### Choose the app you are sending from",
            view=SendingPaymentView(source)
        )


class CurrencyView(View):

    def __init__(self):

        super().__init__(timeout=300)

        self.add_item(
            CurrencySelect()
        )


# =========================================================
# SENDING PAYMENT METHOD
# =========================================================

class SendingPaymentSelect(Select):

    def __init__(self, source):

        self.source = source

        options = [
            discord.SelectOption(
                label=method
            )
            for method in PAYMENT_METHODS[source]
        ]

        super().__init__(
            placeholder="Choose payment app...",
            options=options
        )

    async def callback(self, interaction):

        payment = self.values[0]

        await interaction.response.edit_message(
            content="### Select the Currency you are receiving",
            view=ReceivingCurrencyView(
                source=self.source,
                payment=payment,
                sending_crypto=None
            )
        )


class SendingPaymentView(View):

    def __init__(self, source):

        super().__init__(timeout=300)

        self.add_item(
            SendingPaymentSelect(source)
        )


# =========================================================
# SENDING CRYPTO
# =========================================================

class SendingCryptoSelect(Select):

    def __init__(self):

        options = [
            discord.SelectOption(
                label=crypto
            )
            for crypto in CRYPTO
        ]

        super().__init__(
            placeholder="Choose crypto...",
            options=options
        )

    async def callback(self, interaction):

        sending_crypto = self.values[0]

        await interaction.response.edit_message(
            content="### Select the Currency you are receiving",
            view=ReceivingCurrencyView(
                source="CRYPTO",
                payment=None,
                sending_crypto=sending_crypto
            )
        )


class SendingCryptoView(View):

    def __init__(self):

        super().__init__(timeout=300)

        self.add_item(
            SendingCryptoSelect()
        )


# =========================================================
# RECEIVING CURRENCY
# =========================================================

class ReceivingCurrencySelect(Select):

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
                label="INR",
                description="Receive Indian Rupee"
            ),
            discord.SelectOption(
                label="NPR",
                description="Receive Nepalese Rupee"
            ),
            discord.SelectOption(
                label="BDT",
                description="Receive Bangladeshi Taka"
            ),
            discord.SelectOption(
                label="Crypto",
                description="Receive cryptocurrency"
            )
        ]

        super().__init__(
            placeholder="Select receiving currency...",
            options=options
        )

    async def callback(self, interaction):

        receiving = self.values[0]

        # Crypto receiving → choose receiving crypto
        if receiving == "Crypto":

            await interaction.response.edit_message(
                content="### Choose the Crypto you are receiving",
                view=ReceivingCryptoView(
                    source=self.source,
                    payment=self.payment,
                    sending_crypto=self.sending_crypto
                )
            )

            return

        # Fiat receiving → NO receiving payment-app step
        await interaction.response.edit_message(
            content=(
                "### Enter your amount\n\n"
                + (
                    "**Amount will be entered in USD ($).**"
                    if self.source == "CRYPTO"
                    else "**Enter the amount you are sending.**"
                )
            ),
            view=KeypadView(
                source=self.source,
                payment=self.payment,
                sending_crypto=self.sending_crypto,
                receiving_currency=receiving,
                receiving_crypto=None
            )
        )


class ReceivingCurrencyView(View):

    def __init__(
        self,
        source,
        payment,
        sending_crypto
    ):

        super().__init__(timeout=300)

        self.add_item(
            ReceivingCurrencySelect(
                source,
                payment,
                sending_crypto
            )
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
                label=crypto
            )
            for crypto in CRYPTO
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
                "**Amount will be entered in USD ($).**"
                if self.source == "CRYPTO"
                else
                "### Enter your amount\n\n"
                "**Enter the amount you are sending.**"
            ),
            view=KeypadView(
                source=self.source,
                payment=self.payment,
                sending_crypto=self.sending_crypto,
                receiving_currency="CRYPTO",
                receiving_crypto=receiving_crypto
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
        receiving_currency,
        receiving_crypto
    ):

        super().__init__(timeout=300)

        self.source = source
        self.payment = payment
        self.sending_crypto = sending_crypto
        self.receiving_currency = receiving_currency
        self.receiving_crypto = receiving_crypto

        self.amount = ""

        # -------------------------------------------------
        # ROW 1
        # -------------------------------------------------

        for number in ["1", "2", "3"]:

            button = Button(
                label=number,
                style=discord.ButtonStyle.secondary,
                row=0
            )

            button.callback = self.number_callback(
                number
            )

            self.add_item(button)

        # -------------------------------------------------
        # ROW 2
        # -------------------------------------------------

        for number in ["4", "5", "6"]:

            button = Button(
                label=number,
                style=discord.ButtonStyle.secondary,
                row=1
            )

            button.callback = self.number_callback(
                number
            )

            self.add_item(button)

        # -------------------------------------------------
        # ROW 3
        # -------------------------------------------------

        for number in ["7", "8", "9"]:

            button = Button(
                label=number,
                style=discord.ButtonStyle.secondary,
                row=2
            )

            button.callback = self.number_callback(
                number
            )

            self.add_item(button)

        # -------------------------------------------------
        # ROW 4
        # -------------------------------------------------

        dot = Button(
            label=".",
            style=discord.ButtonStyle.secondary,
            row=3
        )

        dot.callback = self.number_callback(".")

        self.add_item(dot)

        zero = Button(
            label="0",
            style=discord.ButtonStyle.secondary,
            row=3
        )

        zero.callback = self.number_callback("0")

        self.add_item(zero)

        delete = Button(
            label="⌫",
            style=discord.ButtonStyle.danger,
            row=3
        )

        delete.callback = self.delete_callback

        self.add_item(delete)

        # -------------------------------------------------
        # ROW 5
        # -------------------------------------------------

        confirm = Button(
            label="Confirm",
            style=discord.ButtonStyle.success,
            row=4
        )

        confirm.callback = self.confirm_callback

        self.add_item(confirm)

    # =====================================================
    # NUMBER BUTTON
    # =====================================================

    def number_callback(self, number):

        async def callback(interaction):

            # Prevent multiple decimal points
            if number == "." and "." in self.amount:

                await interaction.response.send_message(
                    "❌ You can only use one decimal point.",
                    ephemeral=True
                )

                return

            # Don't allow too many characters
            if len(self.amount) >= 15:

                await interaction.response.send_message(
                    "❌ Maximum amount length reached.",
                    ephemeral=True
                )

                return

            # If first button is "."
            if number == "." and not self.amount:

                self.amount = "0."

            else:

                self.amount += number

            await interaction.response.edit_message(
                content=self.amount_text(),
                view=self
            )

        return callback

    # =====================================================
    # DELETE
    # =====================================================

    async def delete_callback(
        self,
        interaction
    ):

        self.amount = self.amount[:-1]

        await interaction.response.edit_message(
            content=self.amount_text(),
            view=self
        )

    # =====================================================
    # AMOUNT TEXT
    # =====================================================

    def amount_text(self):

        if self.source == "CRYPTO":

            return (
                "### Enter your amount\n\n"
                "**USD ($)**\n"
                f"Amount: `${self.amount or '0'}`"
            )

        if self.source == "INR":

            symbol = "₹"

        elif self.source == "NPR":

            symbol = "रू"

        elif self.source == "BDT":

            symbol = "৳"

        else:

            symbol = ""

        return (
            "### Enter your amount\n\n"
            f"Amount: `{symbol}{self.amount or '0'}`"
        )

    # =====================================================
    # CONFIRM
    # =====================================================

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

        # -------------------------------------------------
        # DETERMINE EXCHANGE TYPE
        # -------------------------------------------------

        if self.source == "CRYPTO":

            exchange_type = get_exchange_type(
                "CRYPTO",
                self.receiving_currency
            )

        else:

            exchange_type = get_exchange_type(
                self.source,
                "CRYPTO"
            )

        if exchange_type == "UNKNOWN":

            await interaction.response.send_message(
                "❌ Unable to determine exchange type.",
                ephemeral=True
            )

            return

        await interaction.response.edit_message(
            content="⏳ Creating your ticket...",
            view=None
        )

        await create_ticket(
            interaction=interaction,
            exchange_type=exchange_type,
            source=self.source,
            payment=self.payment,
            sending_crypto=self.sending_crypto,
            receiving_currency=self.receiving_currency,
            receiving_crypto=self.receiving_crypto,
            amount=amount
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
    receiving_currency,
    receiving_crypto,
    amount
):

    guild = interaction.guild

    # -----------------------------------------------------
    # GLOBAL TICKET NUMBER
    # -----------------------------------------------------

    counter = database.get_setting(
        "ticket_counter"
    )

    if counter is None:

        ticket_number = 1

    else:

        ticket_number = int(counter) + 1

    database.set_setting(
        "ticket_counter",
        ticket_number
    )

    # -----------------------------------------------------
    # STAFF ROLE
    # -----------------------------------------------------

    role_id = get_role_id(
        exchange_type
    )

    # -----------------------------------------------------
    # PERMISSIONS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # FIND / CREATE CATEGORY
    # -----------------------------------------------------

    category = None

    for cat in guild.categories:

        if cat.name.lower() == "winter tickets":

            category = cat
            break

    if category is None:

        category = await guild.create_category(
            "Winter Tickets"
        )

    # -----------------------------------------------------
    # CHANNEL NAME
    # -----------------------------------------------------

    channel_name = (
        f"{exchange_type.lower()}-"
        f"{ticket_number:03d}"
    )

    channel = await guild.create_text_channel(
        channel_name,
        category=category,
        overwrites=overwrites,
        reason="Winter Exchange ticket"
    )

    # -----------------------------------------------------
    # SAVE TICKET
    # -----------------------------------------------------

    database.create_ticket(
        channel_id=channel.id,
        ticket_number=ticket_number,
        user_id=interaction.user.id,
        exchange_type=exchange_type,
        sending_currency=source,
        payment_method=payment,
        sending_crypto=sending_crypto,
        receiving_crypto=receiving_crypto,
        amount=amount
    )

    # -----------------------------------------------------
    # CALCULATE RECEIVING AMOUNT
    # -----------------------------------------------------

    if exchange_type == "I2C":

        receiving_amount = amount / 104

        from_text = f"₹{amount:g}"

        to_text = f"${receiving_amount:.2f}"

    elif exchange_type == "N2C":

        receiving_amount = amount / 165

        from_text = f"रू{amount:g}"

        to_text = f"${receiving_amount:.2f}"

    elif exchange_type == "B2C":

        receiving_amount = amount / 142

        from_text = f"৳{amount:g}"

        to_text = f"${receiving_amount:.2f}"

    elif exchange_type == "C2I":

        receiving_amount = amount * 100

        from_text = f"${amount:g}"

        to_text = f"₹{receiving_amount:.2f}"

    elif exchange_type == "C2N":

        receiving_amount = amount * 150

        from_text = f"${amount:g}"

        to_text = f"रू{receiving_amount:.2f}"

    elif exchange_type == "C2B":

        receiving_amount = amount * 118

        from_text = f"${amount:g}"

        to_text = f"৳{receiving_amount:.2f}"

    elif exchange_type == "C2C":

        receiving_amount = amount * 0.95

        from_text = f"${amount:g}"

        to_text = f"${receiving_amount:.2f}"

    else:

        from_text = str(amount)
        to_text = "Unknown"

    # -----------------------------------------------------
    # EXCHANGE EMBED
    # -----------------------------------------------------

    embed = discord.Embed(
        title="💱 Winter Exchange",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="From",
        value=from_text,
        inline=True
    )

    embed.add_field(
        name="To",
        value=to_text,
        inline=True
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

    if payment:

        embed.add_field(
            name="Sending Payment Method",
            value=payment,
            inline=False
        )

    if sending_crypto:

        embed.add_field(
            name="Sending Crypto",
            value=sending_crypto,
            inline=False
        )

    if receiving_currency:

        embed.add_field(
            name="Receiving Currency",
            value=receiving_currency,
            inline=False
        )

    if receiving_crypto:

        embed.add_field(
            name="Receiving Crypto",
            value=receiving_crypto,
            inline=False
        )

    embed.set_footer(
        text=(
            f"Winter Exchange • "
            f"Ticket #{ticket_number:03d}"
        )
    )

    # -----------------------------------------------------
    # SEND EXCHANGE EMBED
    # -----------------------------------------------------

    await channel.send(
        content=interaction.user.mention,
        embed=embed
    )

    # -----------------------------------------------------
    # SAFETY EMBED
    # -----------------------------------------------------

    safety = discord.Embed(
        title="⚠️ Transaction Safety",
        description=(
            "For your safety, always complete transactions "
            "within your ticket, where funds are securely "
            "held for both parties.\n\n"

            "> - We are not responsible for any losses or "
            "scams resulting from transactions conducted "
            "outside the ticket system.\n\n"

            "> - Anyone asking you to move the trade outside "
            "the ticket is very likely attempting to scam you."
        ),
        color=discord.Color.orange()
    )

    await channel.send(
        embed=safety,
        view=TicketView()
    )

    # -----------------------------------------------------
    # FINISH CREATION
    # -----------------------------------------------------

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
            style=discord.ButtonStyle.primary,
            custom_id="winter_claim_ticket"
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

        if ticket[11]:

            await interaction.response.send_message(
                "❌ This ticket is already closed.",
                ephemeral=True
            )
            return

        role_id = get_role_id(ticket[4])

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
            style=discord.ButtonStyle.success,
            custom_id="winter_done_ticket"
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

        if ticket[11]:

            await interaction.response.send_message(
                "❌ This ticket is already closed.",
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
            view=ReceivedView(customer.id)
        )


# =========================================================
# RECEIVED BUTTON
# =========================================================

class ReceivedButton(Button):

    def __init__(self, customer_id):

        self.customer_id = customer_id

        super().__init__(
            label="Yes, Received",
            style=discord.ButtonStyle.success,
            custom_id=f"winter_received_{customer_id}"
        )

    async def callback(self, interaction):

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

        amount = float(ticket[9])

        # -------------------------------------------------
        # REP AMOUNT
        # -------------------------------------------------

        if ticket[4] == "I2C":

            rep_amount = amount / 104

        elif ticket[4] == "N2C":

            rep_amount = amount / 165

        elif ticket[4] == "B2C":

            rep_amount = amount / 142

        elif ticket[4] == "C2C":

            rep_amount = amount * 0.95

        else:

            rep_amount = amount

        # -------------------------------------------------
        # FINAL CONFIRMATION
        # -------------------------------------------------

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

        # -------------------------------------------------
        # SEND LOG
        # -------------------------------------------------

        await send_log(
            interaction.guild,
            interaction.channel,
            ticket,
            exchanger_id
        )

        # -------------------------------------------------
        # CLOSE DATABASE
        # -------------------------------------------------

        database.close_ticket(
            interaction.channel.id
        )

        # -------------------------------------------------
        # CLOSE CHANNEL VISIBILITY
        # -------------------------------------------------

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

        await interaction.channel.send(
            "🔒 **Ticket closed.**\n"
            "The exchange has been completed."
        )


# =========================================================
# RECEIVED VIEW
# =========================================================

class ReceivedView(View):

    def __init__(self, customer_id):

        super().__init__(
            timeout=None
        )

        self.add_item(
            ReceivedButton(customer_id)
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

    except (ValueError, TypeError):

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

    amount = float(ticket[9])

    if ticket[4] == "I2C":

        from_text = f"₹{amount:g}"
        to_text = f"${amount / 104:.2f}"

    elif ticket[4] == "N2C":

        from_text = f"रू{amount:g}"
        to_text = f"${amount / 165:.2f}"

    elif ticket[4] == "B2C":

        from_text = f"৳{amount:g}"
        to_text = f"${amount / 142:.2f}"

    elif ticket[4] == "C2I":

        from_text = f"${amount:g}"
        to_text = f"₹{amount * 100:.2f}"

    elif ticket[4] == "C2N":

        from_text = f"${amount:g}"
        to_text = f"रू{amount * 150:.2f}"

    elif ticket[4] == "C2B":

        from_text = f"${amount:g}"
        to_text = f"৳{amount * 118:.2f}"

    elif ticket[4] == "C2C":

        from_text = f"${amount:g}"
        to_text = f"${amount * 0.95:.2f}"

    else:

        from_text = str(amount)
        to_text = "Unknown"

    exchanger_mention = (
        exchanger.mention
        if exchanger
        else f"<@{exchanger_id}>"
    )

    exchanger_name = (
        exchanger.name
        if exchanger
        else "Unknown"
    )

    customer_text = (
        customer.mention
        if customer
        else f"<@{ticket[3]}>"
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

    embed.add_field(
        name="Exchange Type:",
        value=ticket[4],
        inline=False
    )

    if ticket[6]:

        embed.add_field(
            name="Sending Payment Method:",
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
# COMMANDS
# =========================================================

@bot.command(name="help")
async def help_command(ctx):

    embed = discord.Embed(
        title="❄️ Winter Exchange — Help",
        description=(
            "**Admin Commands**\n"
            "`.exchpanel #channel` — Send exchange panel\n"
            "`.exchlog #channel` — Set exchange log channel\n"
            "`.exchlogs #channel` — Alias of exchlog\n"
            "`.I2C @role` — Set INR → Crypto staff role\n"
            "`.C2I @role` — Set Crypto → INR staff role\n"
            "`.C2C @role` — Set Crypto → Crypto staff role\n"
            "`.N2C @role` — Set NPR → Crypto staff role\n"
            "`.C2N @role` — Set Crypto → NPR staff role\n"
            "`.B2C @role` — Set BDT → Crypto staff role\n"
            "`.C2B @role` — Set Crypto → BDT staff role\n"
            "`.delete` — Delete the current ticket\n"
            "`.reopen` — Reopen the current ticket\n\n"
            "**Ticket Commands**\n"
            "`.deal` — Claim the exchange ticket\n"
            "`.done` — Mark the exchange as completed"
        ),
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed)


@bot.command(name="exchpanel")
@is_admin()
async def exchpanel(ctx, channel: discord.TextChannel):

    embed = discord.Embed(
        title="Winter Ticket Panel",
        description=(
            "# `Winter Exchanges`\n\n"
            "> Creating a ticket means you accept our terms and conditions.\n\n"
            "> **Click on the buttons to Interact**\n"
            "> - Create Ticket - Open a Exchange ticket\n"
            "> - Rate - Check current exchange rates\n\n"
            "### NOTE:\n"
            "> - Third-party payments are strictly prohibited.\n"
            "> - We do not cover transaction fees.\n"
            "> - Preferring Wallet Payment ( Eg . Dhani , Nye , Mbk, omni , "
            "Fampay, UPI LITE ) etc\n\n"
            "> - Do not pay more than the exchanger's stated limit.\n"
            "> - Do not proceed with the deal until the exchanger has claimed "
            "the ticket and the ticket has been renamed.\n"
            "> - We Won't be liable and won't refund if paid the exchanger "
            "above his limit directly without mm"
        ),
        color=discord.Color.blue()
    )

    await channel.send(embed=embed, view=PanelView())

    await ctx.send(
        f"✅ Exchange panel sent to {channel.mention}.",
        delete_after=5
    )


@bot.command(name="exchlog", aliases=["exchlogs"])
@is_admin()
async def exchlog(ctx, channel: discord.TextChannel):

    database.set_setting("log_channel", channel.id)

    await ctx.send(
        f"✅ Exchange log channel set to {channel.mention}.",
        delete_after=5
    )


# =========================================================
# EXCHANGE ROLE COMMANDS
# =========================================================

async def set_exchange_role(ctx, exchange_type, role):

    database.set_setting(
        f"role_{exchange_type}",
        role.id
    )

    await ctx.send(
        f"✅ **{exchange_type}** staff role set to {role.mention}.",
        delete_after=5
    )


@bot.command(name="I2C")
@is_admin()
async def i2c_role(ctx, role: discord.Role):
    await set_exchange_role(ctx, "I2C", role)


@bot.command(name="C2I")
@is_admin()
async def c2i_role(ctx, role: discord.Role):
    await set_exchange_role(ctx, "C2I", role)


@bot.command(name="C2C")
@is_admin()
async def c2c_role(ctx, role: discord.Role):
    await set_exchange_role(ctx, "C2C", role)


@bot.command(name="N2C")
@is_admin()
async def n2c_role(ctx, role: discord.Role):
    await set_exchange_role(ctx, "N2C", role)


@bot.command(name="C2N")
@is_admin()
async def c2n_role(ctx, role: discord.Role):
    await set_exchange_role(ctx, "C2N", role)


@bot.command(name="B2C")
@is_admin()
async def b2c_role(ctx, role: discord.Role):
    await set_exchange_role(ctx, "B2C", role)


@bot.command(name="C2B")
@is_admin()
async def c2b_role(ctx, role: discord.Role):
    await set_exchange_role(ctx, "C2B", role)


# =========================================================
# DEAL / CLAIM
# =========================================================

@bot.command(name="deal")
async def deal_command(ctx):

    if not ctx.guild:
        return

    ticket = database.get_ticket(ctx.channel.id)

    if not ticket:
        await ctx.send(
            "❌ This command can only be used inside an exchange ticket.",
            delete_after=5
        )
        return

    if ticket[11]:
        await ctx.send(
            "❌ This ticket is closed.",
            delete_after=5
        )
        return

    exchange_type = ticket[4]
    role_id = database.get_setting(f"role_{exchange_type}")

    if not role_id:
        await ctx.send(
            "❌ No staff role has been configured for this exchange type.",
            delete_after=5
        )
        return

    role = ctx.guild.get_role(int(role_id))

    if not role:
        await ctx.send(
            "❌ The configured staff role no longer exists.",
            delete_after=5
        )
        return

    if role not in ctx.author.roles and not ctx.author.guild_permissions.administrator:
        await ctx.send(
            "❌ You don't have permission to claim this ticket.",
            delete_after=5
        )
        return

    if ticket[10]:
        claimer = ctx.guild.get_member(ticket[10])

        if claimer:
            await ctx.send(
                f"❌ This ticket is already claimed by {claimer.mention}.",
                delete_after=5
            )
        else:
            await ctx.send(
                "❌ This ticket is already claimed.",
                delete_after=5
            )
        return

    database.claim_ticket(
        ctx.channel.id,
        ctx.author.id
    )

    new_name = f"{ctx.channel.name}-{ctx.author.name}"

    try:
        await ctx.channel.edit(name=new_name)
    except discord.HTTPException:
        pass

    await ctx.send(
        f"🤝 **Deal claimed by {ctx.author.mention}**\n"
        f"Ticket renamed to `{new_name}`."
    )


# =========================================================
# DONE
# =========================================================

@bot.command(name="done")
async def done_command(ctx):

    ticket = database.get_ticket(ctx.channel.id)

    if not ticket:
        await ctx.send(
            "❌ This command can only be used inside an exchange ticket.",
            delete_after=5
        )
        return

    if ticket[11]:
        await ctx.send(
            "❌ This ticket is already closed.",
            delete_after=5
        )
        return

    if ticket[10] != ctx.author.id:
        await ctx.send(
            "❌ Only the exchanger who claimed this ticket can use `.done`.",
            delete_after=5
        )
        return

    customer = ctx.guild.get_member(ticket[3])

    if not customer:
        await ctx.send(
            "❌ The customer could not be found.",
            delete_after=5
        )
        return

    embed = discord.Embed(
        title="Exchange Completed?",
        description=(
            f"Hey {customer.mention}\n\n"
            "The Exchange has been Done?\n\n"
            "Just for an small Confirmation after reciving payment "
            "click on **Yes, Received** Button"
        ),
        color=discord.Color.green()
    )

    await ctx.send(
        content=customer.mention,
        embed=embed,
        view=ReceivedView(customer.id)
    )


# =========================================================
# DELETE
# =========================================================

@bot.command(name="delete")
@is_admin()
async def delete_command(ctx):

    ticket = database.get_ticket(ctx.channel.id)

    if not ticket:
        await ctx.send(
            "❌ This is not an exchange ticket.",
            delete_after=5
        )
        return

    await ctx.send(
        "🗑️ Deleting this ticket...",
        delete_after=2
    )

    await asyncio.sleep(1)

    try:
        await ctx.channel.delete(
            reason=f"Ticket deleted by {ctx.author}"
        )
    except discord.NotFound:
        pass


# =========================================================
# REOPEN
# =========================================================

@bot.command(name="reopen")
@is_admin()
async def reopen_command(ctx):

    ticket = database.get_ticket(ctx.channel.id)

    if not ticket:
        await ctx.send(
            "❌ This is not an exchange ticket.",
            delete_after=5
        )
        return

    database.reopen_ticket(ctx.channel.id)

    customer = ctx.guild.get_member(ticket[3])

    role_id = database.get_setting(
        f"role_{ticket[4]}"
    )

    role = None

    if role_id:
        role = ctx.guild.get_role(int(role_id))

    overwrites = ctx.channel.overwrites

    overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(
        view_channel=False
    )

    if customer:
        overwrites[customer] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True
        )

    if role:
        overwrites[role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True
        )

    try:
        await ctx.channel.edit(
            overwrites=overwrites
        )
    except discord.HTTPException:
        pass

    await ctx.send(
        "🔓 **Ticket reopened successfully.**"
    )


# =========================================================
# COMMAND ERROR HANDLER
# =========================================================

@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ You don't have permission to use this command.",
            delete_after=5
        )
        return

    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            "❌ You don't have permission to use this command.",
            delete_after=5
        )
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"❌ Missing argument: `{error.param.name}`.",
            delete_after=5
        )
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(
            "❌ Invalid argument. Please mention the correct channel or role.",
            delete_after=5
        )
        return

    print(
        f"[COMMAND ERROR] {type(error).__name__}: {error}"
    )


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    if not getattr(bot, "_winter_views_added", False):

        bot.add_view(PanelView())
        bot.add_view(TicketView())

        bot._winter_views_added = True

    await bot.change_presence(
        activity=discord.Game(
            name=".help | Winter Exchange"
        )
    )

    print()
    print("=" * 50)
    print("❄️ WINTER EXCHANGE")
    print("=" * 50)
    print(
        f"✅ Logged in as: {bot.user} "
        f"(ID: {bot.user.id})"
    )
    print(
        f"📡 Servers: {len(bot.guilds)}"
    )
    print(
        f"⚙️ Prefix: {PREFIX}"
    )
    print("🚀 Bot is ready!")
    print("=" * 50)


# =========================================================
# START BOT
# =========================================================

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing from the .env file."
    )

bot.run(TOKEN)