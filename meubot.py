import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import hashlib


# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

NAME, DOCUMENT_NUMBER, DOCUMENT_NUMBER_EXCLUDE, DOCUMENT_NUMBER_UPDATE, NAME_UPDATE, PASSWORD = range(6)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    document_number = Column(String)
    password = Column(String)

    def __repr__(self):
        return f"<User(name='{self.name}', DocumentNumber ='{self.document_number}', password ='{self.password}')>"


engine = create_engine('sqlite:///userData.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

user = User()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks for the user's document number."""
    await update.message.reply_text(
        "Olá, bem-vindo ao sistema OzaBot. Eu vou fazer seu cadastro. "
        "Digite /cancel a qualquer momento para sair.\n\n"
        "Por favor, me diga o número do seu documento sem pontuação:"
    )

    return DOCUMENT_NUMBER


async def document_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's document number and asks for their name."""
    user = update.message.from_user
    document_number = update.message.text

    # Check if the user is already registered in the database
    session = Session()
    existing_user = session.query(User).filter(User.document_number == document_number).first()
    session.close()

    if existing_user:
        await update.message.reply_text("Você já está cadastrado no nosso sistema. Por favor escolha outra função.")
        return ConversationHandler.END

    # Store the document number in user_data
    context.user_data['document_number'] = document_number

    await update.message.reply_text("Por favor, me diga seu nome completo:")

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's name and prompts for the password."""
    user = update.message.from_user
    name = update.message.text

    # Store the user's name in user_data
    context.user_data['name'] = name

    await update.message.reply_text("Por favor, digite sua senha:")
    return PASSWORD


async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's password and proceeds with the registration."""
    password = update.message.text

    # Retrieve the name from user_data
    name = context.user_data.get('name')

    # Retrieve the document number from user_data
    document_number = context.user_data.get('document_number')

    # Store the user's name, document number, and hashed password in the database
    session = Session()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash the password
    user = User(name=name, document_number=document_number, password=hashed_password)
    session.add(user)
    session.commit()
    session.close()

    await update.message.reply_text("Usuário cadastrado com sucesso! Obrigado por usar nosso sistema!")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Operação cancelada pelo usuário. Até uma proxima vez!")

    # Close the database session
    session = context["session"]
    session.close()

    return ConversationHandler.END


async def exclude(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Exclude' command."""
    await update.message.reply_text("Por favor, digite o número do documento do usuário que deseja excluir:")

    return DOCUMENT_NUMBER_EXCLUDE


async def document_number_exclude(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Checks if the user exists in the database and deletes them."""
    document_number = update.message.text

    # Check if the user is registered in the database
    session = Session()
    existing_user = session.query(User).filter(User.document_number == document_number).first()

    if existing_user:
        # User exists, delete them from the database
        session.delete(existing_user)
        session.commit()
        await update.message.reply_text("Usuário excluído com sucesso.")
    else:
        # User not found in the database
        await update.message.reply_text("Usuário não encontrado.")

    session.close()

    return ConversationHandler.END


async def update_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Update' command."""
    await update.message.reply_text("Por favor, digite o número do documento do usuário que deseja atualizar:")

    return DOCUMENT_NUMBER_UPDATE


async def document_number_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Checks if the user exists in the database and updates their name."""
    document_number = update.message.text

    # Check if the user is registered in the database
    session = Session()
    existing_user = session.query(User).filter(User.document_number == document_number).first()

    if existing_user:
        # User exists, prompt for the updated name
        await update.message.reply_text("Usuário encontrado. Por favor, digite o novo nome do usuário:")
        context.user_data['document_number'] = document_number
        return NAME_UPDATE
    else:
        # User not found in the database
        await update.message.reply_text("Usuário não encontrado.")

    session.close()

    return ConversationHandler.END


async def name_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Updates the user's name."""
    user = update.message.from_user
    name = update.message.text

    # Retrieve the document number from user_data
    document_number = context.user_data.get('document_number')

    # Update the user's name in the database
    session = Session()
    existing_user = session.query(User).filter(User.document_number == document_number).first()
    existing_user.name = name
    session.commit()
    session.close()

    await update.message.reply_text("Nome do usuário atualizado com sucesso.")

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("6118529672:AAHZBakVYjD0P28HHh9IaZ4qPBdds9LdHUs").build()

    # Add conversation handler with the states FULL NAME and DOCUMENT NUMBER
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("update", update_user),
            CommandHandler("exclude", exclude)
        ],
        states={
            DOCUMENT_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, document_number)],
            DOCUMENT_NUMBER_EXCLUDE: [MessageHandler(filters.TEXT & ~filters.COMMAND, document_number_exclude)],
            DOCUMENT_NUMBER_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, document_number_update)],
            NAME_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_update)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    # Setup logging and other configurations if needed
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    # Call the main function
    main()
