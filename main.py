from app import ElectroServiceApp
from repository import init_database


if __name__ == "__main__":
    init_database()
    app = ElectroServiceApp()
    app.mainloop()
