# library_management_system.py
import sqlite3
from datetime import datetime, timedelta

class LibraryManagementSystem:
    def __init__(self, db_name='library.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_db_connection(self):
        """Establishes and returns a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initializes the database and creates the necessary tables if they don't exist."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # Create 'books' table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE,
            published_year INTEGER,
            is_available BOOLEAN NOT NULL DEFAULT 1
        )
        ''')

        # Create 'members' table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
        ''')

        # Create 'transactions' table to log all borrow/return activity
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (member_id) REFERENCES members (id)
        )
        ''')

        conn.commit()
        conn.close()
        print("Database initialized successfully.")

    # --- BOOK FUNCTIONS ---
    def add_book(self):
        """Adds a new book to the library."""
        print("\n--- Add New Book ---")
        try:
            title = input("Enter book title: ").strip()
            author = input("Enter book author: ").strip()
            isbn = input("Enter book ISBN: ").strip()
            year = input("Enter publication year: ").strip()
            
            if not title or not author:
                print("Error: Title and author are required.")
                return
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO books (title, author, isbn, published_year, is_available)
            VALUES (?, ?, ?, ?, ?)
            ''', (title, author, isbn, year, True))
            conn.commit()
            print(f"✓ Book '{title}' added successfully.")
        except sqlite3.IntegrityError:
            print("✗ Error: A book with this ISBN already exists.")
        except Exception as e:
            print(f"✗ An error occurred: {e}")
        finally:
            conn.close()

    def view_all_books(self):
        """Displays all books in the library."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM books ORDER BY title')
            books = cursor.fetchall()
            
            if not books:
                print("\nNo books found in the library.")
                return
            
            print(f"\n{'--- Book List ---':^50}")
            print(f"{'ID':<5} {'Title':<20} {'Author':<15} {'Status':<10}")
            print("-" * 50)
            for book in books:
                status = "Available" if book['is_available'] else "Borrowed"
                print(f"{book['id']:<5} {book['title'][:18]:<20} {book['author'][:13]:<15} {status:<10}")
        except Exception as e:
            print(f"✗ An error occurred: {e}")
        finally:
            conn.close()

    def search_books(self):
        """Searches for books by title or author."""
        search_term = input("\nEnter title or author to search for: ").strip()
        if not search_term:
            print("Please enter a search term.")
            return
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ?
            ORDER BY title
            ''', (f'%{search_term}%', f'%{search_term}%'))
            books = cursor.fetchall()
            
            if not books:
                print("No books found matching your search.")
                return
            
            print(f"\n{'--- Search Results ---':^50}")
            print(f"{'ID':<5} {'Title':<20} {'Author':<15} {'Status':<10}")
            print("-" * 50)
            for book in books:
                status = "Available" if book['is_available'] else "Borrowed"
                print(f"{book['id']:<5} {book['title'][:18]:<20} {book['author'][:13]:<15} {status:<10}")
        except Exception as e:
            print(f"✗ An error occurred: {e}")
        finally:
            conn.close()

    # --- MEMBER FUNCTIONS ---
    def add_member(self):
        """Adds a new library member."""
        print("\n--- Add New Member ---")
        try:
            name = input("Enter member name: ").strip()
            email = input("Enter member email: ").strip()
            
            if not name or not email:
                print("Error: Name and email are required.")
                return
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO members (name, email) VALUES (?, ?)', (name, email))
            conn.commit()
            print(f"✓ Member '{name}' added successfully.")
        except sqlite3.IntegrityError:
            print("✗ Error: A member with this email already exists.")
        except Exception as e:
            print(f"✗ An error occurred: {e}")
        finally:
            conn.close()

    def view_all_members(self):
        """Displays all library members."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM members ORDER BY name')
            members = cursor.fetchall()
            
            if not members:
                print("\nNo members registered.")
                return
            
            print(f"\n{'--- Member List ---':^40}")
            print(f"{'ID':<5} {'Name':<20} {'Email':<15}")
            print("-" * 40)
            for member in members:
                print(f"{member['id']:<5} {member['name'][:18]:<20} {member['email'][:13]:<15}")
        except Exception as e:
            print(f"✗ An error occurred: {e}")
        finally:
            conn.close()

    # --- TRANSACTION FUNCTIONS ---
    def borrow_book(self):
        """Allows a member to borrow a book."""
        print("\n--- Borrow a Book ---")
        try:
            book_id = int(input("Enter the ID of the book to borrow: "))
            member_id = int(input("Enter your member ID: "))
            
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Check if book exists and is available
            cursor.execute('SELECT title, is_available FROM books WHERE id = ?', (book_id,))
            book = cursor.fetchone()
            if not book:
                print("✗ Error: Book not found.")
                return
            if not book['is_available']:
                print("✗ Error: Book is already borrowed.")
                return

            # Check if member exists
            cursor.execute('SELECT name FROM members WHERE id = ?', (member_id,))
            member = cursor.fetchone()
            if not member:
                print("✗ Error: Member not found.")
                return

            # Calculate dates
            borrow_date = datetime.now().strftime('%Y-%m-%d')
            due_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

            # Create transaction record
            cursor.execute('''
            INSERT INTO transactions (book_id, member_id, borrow_date, due_date)
            VALUES (?, ?, ?, ?)
            ''', (book_id, member_id, borrow_date, due_date))

            # Update book availability
            cursor.execute('UPDATE books SET is_available = 0 WHERE id = ?', (book_id,))

            conn.commit()
            print(f"✓ Book '{book['title']}' borrowed successfully by {member['name']}.")
            print(f"  Due date: {due_date}")
        except ValueError:
            print("✗ Please enter valid numeric IDs.")
        except Exception as e:
            print(f"✗ An error occurred: {e}")
        finally:
            conn.close()

    def return_book(self):
        """Allows a member to return a borrowed book."""
        print("\n--- Return a Book ---")
        try:
            book_id = int(input("Enter the ID of the book to return: "))
            
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Find active transaction
            cursor.execute('''
            SELECT t.id, b.title, m.name 
            FROM transactions t
            JOIN books b ON t.book_id = b.id
            JOIN members m ON t.member_id = m.id
            WHERE t.book_id = ? AND t.return_date IS NULL
            ''', (book_id,))
            transaction = cursor.fetchone()

            if not transaction:
                print("✗ Error: No active borrow record found for this book.")
                return

            # Update transaction with return date
            return_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('UPDATE transactions SET return_date = ? WHERE id = ?', 
                          (return_date, transaction['id']))

            # Update book availability
            cursor.execute('UPDATE books SET is_available = 1 WHERE id = ?', (book_id,))

            conn.commit()
            print(f"✓ Book '{transaction['title']}' returned successfully by {transaction['name']}.")
        except ValueError:
            print("✗ Please enter a valid numeric book ID.")
        except Exception as e:
            print(f"✗ An error occurred: {e}")
        finally:
            conn.close()

    def view_borrowed_books(self):
        """Displays all currently borrowed books."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
            SELECT
                b.id as book_id,
                b.title,
                m.name as member_name,
                t.borrow_date,
                t.due_date
            FROM transactions t
            JOIN books b ON t.book_id = b.id
            JOIN members m ON t.member_id = m.id
            WHERE t.return_date IS NULL
            ORDER BY t.due_date
            ''')
            borrowed_books = cursor.fetchall()
            
            if not borrowed_books:
                print("\nNo books are currently borrowed.")
                return
            
            print(f"\n{'--- Currently Borrowed Books ---':^60}")
            print(f"{'Book':<20} {'Borrowed by':<15} {'Borrow Date':<12} {'Due Date':<12}")
            print("-" * 60)
            for book in borrowed_books:
                print(f"{book['title'][:18]:<20} {book['member_name'][:13]:<15} "
                      f"{book['borrow_date']:<12} {book['due_date']:<12}")
        except Exception as e:
            print(f"✗ An error occurred: {e}")
        finally:
            conn.close()

    def display_menu(self):
        """Displays the main menu."""
        print("\n" + "="*50)
        print("        LIBRARY MANAGEMENT SYSTEM")
        print("="*50)
        print("1.  Add a new book")
        print("2.  View all books")
        print("3.  Search for a book")
        print("4.  Add a new member")
        print("5.  View all members")
        print("6.  Borrow a book")
        print("7.  Return a book")
        print("8.  View borrowed books")
        print("9.  Exit")
        print("="*50)

    def run(self):
        """Main program loop."""
        print("Welcome to the Library Management System!")
        
        while True:
            self.display_menu()
            choice = input("\nEnter your choice (1-9): ").strip()

            if choice == '1':
                self.add_book()
            elif choice == '2':
                self.view_all_books()
            elif choice == '3':
                self.search_books()
            elif choice == '4':
                self.add_member()
            elif choice == '5':
                self.view_all_members()
            elif choice == '6':
                self.borrow_book()
            elif choice == '7':
                self.return_book()
            elif choice == '8':
                self.view_borrowed_books()
            elif choice == '9':
                print("Thank you for using the Library Management System. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number between 1-9.")
            
            input("\nPress Enter to continue...")

# Run the application
if __name__ == "__main__":
    library_system = LibraryManagementSystem()
    library_system.run()
