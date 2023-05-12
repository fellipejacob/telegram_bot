import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

GENDER, PHOTO, DOCUMENT_NUMBER, NAME = range(4)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    gender = Column(String)
    photo = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    bio = Column(String)

    def __repr__(self):
        return f"<User(chat_id='{self.chat_id}', gender='{self.gender}', photo='{self.photo}', latitude='{self.latitude}', longitude='{self.longitude}', bio='{self.bio}')>"


engine = create_engine('sqlite:///user_data.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

user = User()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""
    reply_keyboard = [["Man", "Woman", "Other"]]

    await update.message.reply_text(
        "Hi! My name is Professor Bot. I will hold a conversation with you. "
        "Send /cancel to stop talking to me.\n\n"
        "Are you a boy or a girl?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Boy or Girl?"
        ),
    )

    return GENDER


async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""
    user = update.message.from_user
    logger.info("Gender of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "I see! Please send me a photo for the registry "
        "or send /skip if you don't want to.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return PHOTO


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and asks for a document number."""
    user = update.message.from_user
    await update.message.reply_text(
        "Great! Now, please send me your document number, or send /skip if you don't want to."
    )

    return DOCUMENT_NUMBER


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the photo and asks for a document number."""
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    await update.message.reply_text(
        "I bet you look great! Now, send me your document number please, or send /skip."
    )

    return DOCUMENT_NUMBER


async def document_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the document number and asks for some info about the user."""
    user = update.message.from_user
    document_number = update.message.text
    logger.info(
        "Document number of %s: %s", user.first_name, document_number
    )
    await update.message.reply_text(
        "Thanks! Finally, tell me your full name."
    )

    return NAME


async def skip_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the document and asks for info about the user."""
    user = update.message.from_user
    logger.info("User %s did not send a document number.", user.first_name)
    await update.message.reply_text(
        "You seem a bit paranoid! At last, tell me something about yourself."
    )

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation."""
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)

    # Store the bio in the database
    session = context.session
    chat_id = user.id
    bio_text = update.message.text
    user = session.query(User).filter_by(chat_id=chat_id).first()
    user.bio = bio_text
    session.commit()

    await update.message.reply_text("Thank you! I hope we can talk again some day.")

    return ConversationHandler.END



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    # Close the database session
    session = context["session"]
    session.close()

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("token_here").build()

    # Add conversation handler with the states GENDER, PHOTO, DOCUMENT and FULL NAME
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GENDER: [MessageHandler(filters.Regex("^(Man|Woman|Other)$"), gender)],
            PHOTO: [MessageHandler(filters.PHOTO, photo),
                    CommandHandler("skip", skip_photo)],
            DOCUMENT_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, document_number),
                CommandHandler("skip", skip_document)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
