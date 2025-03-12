from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from dateutil import parser  # Add this import for flexible date parsing

Base = declarative_base()

class Email(Base):
    __tablename__ = 'emails'
    
    id = Column(String, primary_key=True)
    sender = Column(String)
    recipient = Column(String)
    date = Column(DateTime)
    subject = Column(String)
    content = Column(String)

class EmailDatabase:
    def __init__(self):
        self.engine = create_engine('sqlite:///emails.db')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def store_emails(self, emails):
        session = self.Session()
        try:
            for email in emails:
                # Use dateutil.parser for more flexible date parsing
                try:
                    # Try to parse the date string with dateutil.parser
                    date_obj = parser.parse(email['date'])
                except Exception as e:
                    print(f"Error parsing date '{email['date']}': {str(e)}")
                    # Fallback to current time if date parsing fails
                    date_obj = datetime.datetime.now()
                
                new_email = Email(
                    id=email['id'],
                    sender=email['sender'],
                    recipient=email.get('recipient', ''),
                    date=date_obj,
                    subject=email['subject'],
                    content=email['content']
                )
                session.merge(new_email)
            session.commit()
        except Exception as e:
            print(f"Error storing emails: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()