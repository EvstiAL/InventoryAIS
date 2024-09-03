from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from fpdf import FPDF
from datetime import datetime
from clean import start_console_cleanup_scheduler




app = Flask(__name__)
app.secret_key = 'kljsdhfpiauhpk1j23ho12831h3k1jh2398712h3k1j23'


start_console_cleanup_scheduler(interval_minutes=20)
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к столбцам по имени
    return conn

def get_rooms():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM room")
    rooms = cursor.fetchall()
    conn.close()
    return rooms

def get_items():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT i.*, r.name AS room_name FROM item i JOIN room r ON i.room_id = r.id")
    items = cursor.fetchall()
    conn.close()
    return items
# Создание таблиц в базе данных
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            inventory INTEGER NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            room_id INTEGER,
            FOREIGN KEY (room_id) REFERENCES room (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deleted (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            inventory INTEGER NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            room_id INTEGER,
            mean TEXT NOT NULL,
            note TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            login TEXT NOT NULL,       
            password INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE login = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user





@app.route('/')
def index():
    if 'username' in session:
        conn = get_db_connection()
        rooms = conn.execute('SELECT * FROM room').fetchall()
        conn.close()
        return render_template('index.html', rooms=rooms)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        user = get_user_by_username(username)
        if user:
            session['username'] = user['name'] 
            flash('Вы успешно вошли в систему.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, login, password) VALUES (?, ?, ?)', (username, login, password))
            conn.commit()
            flash('Регистрация прошла успешно! Теперь вы можете войти в систему.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем уже существует!', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/room/<int:room_id>')
def room(room_id):
    conn = get_db_connection()
    room = conn.execute('SELECT * FROM room WHERE id = ?', (room_id,)).fetchone()
    items = conn.execute('SELECT * FROM item WHERE room_id = ?', (room_id,)).fetchall()
    conn.close()


    return render_template('room.html', room=room, items=items, otv = session['username'])

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db_connection()
        conn.execute('INSERT INTO room (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_room.html')

@app.route('/itemOfRoom~<int:room_id>/<int:item_id>', methods = ['POST', 'GET'])
def item(item_id, room_id):
    conn = get_db_connection()
    room = conn.execute('SELECT * FROM room WHERE id = ?', (room_id,)).fetchone()
    items = conn.execute('SELECT * FROM item WHERE id = ?', (item_id,)).fetchone()
    conn.close()
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        inventory = request.form['inventory']
        types = request.form['type']
        category = request.form['category']
        conn = get_db_connection()
        conn.execute('UPDATE item SET name = ?, quantity = ?, inventory = ?, type = ?, category = ? WHERE id = ? ', (name, quantity, inventory, types, category, item_id))
        conn.commit()
        conn.close()
        return redirect(url_for('room', room_id=room_id))
        
    

    return render_template('card_item.html', items=items, room = room)

@app.route('/add_item/<int:room_id>', methods=['GET', 'POST'])
def add_item(room_id):
    connect = get_db_connection()
    roome = connect.execute('SELECT * FROM room WHERE id = ?', (room_id,)).fetchone()
    connect.close()
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        inventory = request.form['inventory']
        types = request.form['type']
        category = request.form['category']
        conn = get_db_connection()
        conn.execute('INSERT INTO item (name, quantity, inventory, type, category, room_id) VALUES (?, ?, ?, ?, ?, ?)', (name, quantity, inventory, types, category, room_id))
        conn.commit()
        conn.close()
        return redirect(url_for('room', room_id=room_id))
    
    return render_template('add_item.html', room_id=room_id, room = roome)

@app.route('/savedoc')
def savedoc():
    return render_template('upload.html')

@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']
    
    if file.filename == '':
        return 'No selected file'
    
    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('index'))
    
    return 'File not allowed'

@app.route('/documents')
def documents():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('documents.html', files=files)

# Просмотр конкретного документа
@app.route('/view/<filename>')
def view_document(filename):
    return render_template('view.html', filename=filename)




# Маршрут для отображения загруженных документов
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/act/move', methods=['GET', 'POST'])
def act():
    if request.method == 'POST':
        item_ids = request.form.getlist('selected_items')
        new_room_id = request.form['new_room_id']
        mover = request.form['mover']
        deputy_director = request.form['deputy_director']
        seler = request.form['seler']

        if item_ids:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM room WHERE id = ?", (new_room_id,))
            new_room_name = cursor.fetchone()['name']

            # Получение названия старого кабинета для всех перемещаемых элементов
            cursor.execute("SELECT DISTINCT room_id FROM item WHERE id IN ({})".format(','.join('?' * len(item_ids))), item_ids)
            old_room_ids = cursor.fetchall()

            old_room_names = []
            for room in old_room_ids:
                cursor.execute("SELECT name FROM room WHERE id = ?", (room['room_id'],))
                old_room_names.append(cursor.fetchone()['name'])


            # Обновление идентификатора кабинета для выбранных элементов
            cursor.execute("UPDATE item SET room_id = ? WHERE id IN ({})".format(','.join('?' * len(item_ids))), [new_room_id] + item_ids)
            conn.commit()

            # Получение перемещенных элементов
            cursor.execute("SELECT i.name, i.quantity, i.inventory, r.name AS room_name FROM item i JOIN room r ON i.room_id = r.id WHERE i.id IN ({})".format(','.join('?' * len(item_ids))), item_ids)
            moved_items = cursor.fetchall()

            conn.close()

            # Создание PDF-документа
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font("timesnewromanpsmt", "", "./static/timesnewromanpsmt.ttf", uni=True)  # Добавьте путь к шрифту
            pdf.set_font("timesnewromanpsmt", size=14)

            pdf.cell(0, 10, "Акт о перемещении имущества", 0, 1, 'C')
            pdf.cell(0, 10, f"Дата: {datetime.now().strftime('%d.%m.%Y')}", 0, 1)
            pdf.cell(0, 10, f"Имущество перемещено из кабинета: {', '.join(old_room_names)} в кабинет: {new_room_name}", 0, 1)

            pdf.cell(0, 10, "Перемещенное имущество:", 0, 1)

            pdf.set_font("timesnewromanpsmt", "", size=12)
            pdf.cell(40, 10, "Название", 1)
            pdf.cell(20, 10, "Кол-во", 1)
            pdf.cell(40, 10, "Инв. Номер", 1)
            pdf.cell(40, 10, "Кабинет", 1, 1)

            pdf.set_font("timesnewromanpsmt", size=12)
            for item in moved_items:
                pdf.cell(40, 10, item['name'], 1)
                pdf.cell(20, 10, str(item['quantity']), 1)
                pdf.cell(40, 10, str(item['inventory']), 1)
                pdf.cell(40, 10, item['room_name'], 1, 1)

            pdf.ln(10)
            pdf.cell(0, 10, f"Зам. директора по ОВ: {deputy_director}", 0, 1)
            pdf.cell(0, 10, f"Лицо, передающее имущество: _________________ {mover}", 0, 1)
            
            pdf.cell(0, 10, f"Принял: ____________ {seler}", 0, 1)

            pdf_filename = f"акт_о_перемещении_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf.output(os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename))

            flash('Имущество успешно перемещено и акт создан.', 'success')
        else:
            flash('Не выбрано ни одного элемента для перемещения.', 'error')

        return redirect(url_for('documents'))
    rooms = get_rooms()
    items = get_items()

    # Получение названий текущих кабинетов для каждого элемента
    current_room_names = {}
    conn = get_db_connection()
    cursor = conn.cursor()
    for item in items:
        cursor.execute("SELECT name FROM room WHERE id = ?", (item['room_id'],))
        current_room_names[item['id']] = cursor.fetchone()['name']
    conn.close()

    return render_template('act.html', rooms=rooms, items=items, current_room_names=current_room_names)


@app.route('/act/write_off', methods=['GET', 'POST'])
def write_off():
    if request.method == 'POST':
        item_ids = request.form.getlist('selected_items')
        mean_spis = request.form['mean_spis']
        note = request.form['note']
        mover = request.form['mover']
        deputy_director = request.form['deputy_director']
        seler = request.form['seler']

        if item_ids:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Fetch details of the items being written off, including room names
            cursor.execute("""
                SELECT i.*, r.name AS room_name 
                FROM item i 
                JOIN room r ON i.room_id = r.id 
                WHERE i.id IN ({})
            """.format(','.join('?' * len(item_ids))), item_ids)
            items = cursor.fetchall()

            # Move items to the deleted table
            for item in items:
                cursor.execute('''
                    INSERT INTO deleted (name, quantity, inventory, type, category, room_id, mean, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item['name'], item['quantity'], item['inventory'], item['type'], item['category'], item['room_id'], mean_spis, note))

            # Delete the items from the item table
            cursor.execute("DELETE FROM item WHERE id IN ({})".format(','.join('?' * len(item_ids))), item_ids)
            conn.commit()

            # Create PDF document
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font("timesnewromanpsmt", "", "./static/timesnewromanpsmt.ttf", uni=True)
            pdf.set_font("timesnewromanpsmt", size=14)

            pdf.cell(0, 10, "Акт о списании имущества", 0, 1, 'C')
            pdf.cell(0, 10, f"Дата: {datetime.now().strftime('%d.%m.%Y')}", 0, 1)
            pdf.cell(0, 10, "Списанное имущество:", 0, 1)

            pdf.cell(40, 10, "Название", 1)
            pdf.cell(20, 10, "Кол-во", 1)
            pdf.cell(40, 10, "Инв. Номер", 1)
            pdf.cell(40, 10, "Кабинет", 1, 1)

            for item in items:
                pdf.cell(40, 10, item['name'], 1)  # Ensure 'name' is correct
                pdf.cell(20, 10, str(item['quantity']), 1)
                pdf.cell(40, 10, str(item['inventory']), 1)
                pdf.cell(40, 10, item['room_name'], 1, 1)  # Use room_name instead of room_id

            pdf.ln(10)
            pdf.cell(0, 10, f"Зам. директора по ОВ: {deputy_director}", 0, 1)
            pdf.cell(0, 10, f"Лицо, передающее имущество: _________________ {mover}", 0, 1)
            pdf.cell(0, 10, f"Принял: ____________ {seler}", 0, 1)

            pdf_filename = f"акт_о_списании_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf.output(os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename))

            flash('Имущество успешно списано и акт создан.', 'success')
        else:
            flash('Не выбрано ни одного элемента для списания.', 'error')

        return redirect(url_for('documents'))

    items = get_items()  # Fetch items from the database
    current_room_names = {}
    conn = get_db_connection()
    cursor = conn.cursor()
    for item in items:
        cursor.execute("SELECT name FROM room WHERE id = ?", (item['room_id'],))
        current_room_names[item['id']] = cursor.fetchone()['name']
    conn.close()    
    return render_template('write_off.html', items=items, current_room_names=current_room_names)

@app.route('/all_inventory_ved')
def allin():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Получение всех категорий из базы данных
    cursor.execute("SELECT DISTINCT category FROM item")
    categories = [row['category'] for row in cursor.fetchall()]

    # Определение выбранной категории
    selected_category = request.args.get('category')

    # Получение всех элементов из базы данных с учетом фильтрации
    if selected_category:
        cursor.execute("SELECT * FROM item WHERE category = ?", (selected_category,))
    else:
        cursor.execute("SELECT * FROM item")
    
    items = cursor.fetchall()

    # Подсчет общего количества имущества
    total_quantity = sum(item['quantity'] for item in items)

    conn.close()
    return render_template('all_im.html', categories=categories, items=items, total_quantity=total_quantity, selected_category=selected_category)

@app.route('/writeOffList')
def wrofflist():
    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("SELECT * FROM deleted")
    
    items = cursor.fetchall()

    # Подсчет общего количества имущества
    total_quantity = sum(item['quantity'] for item in items)

    conn.close()
    return render_template('deleted.html', items=items, total_quantity=total_quantity)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            flash('Файл успешно удалён.', 'success')
        else:
            flash('Файл не найден.', 'error')
    except Exception as e:
        flash(f'Ошибка при удалении файла: {str(e)}', 'error')
    
    return redirect(url_for('documents'))

@app.route('/delete_selected_items/<int:room_id>', methods=['POST'])
def delete_selected_items(room_id):
    selected_items = request.form.getlist('selected_items')
    
    if selected_items:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Удаление выбранных элементов
        cursor.execute("DELETE FROM item WHERE id IN ({})".format(','.join('?' * len(selected_items))), selected_items)
        conn.commit()
        conn.close()
        
        flash('Выбранные элементы успешно удалены.', 'success')
    else:
        flash('Не выбрано ни одного элемента для удаления.', 'error')
    
    return redirect(url_for('room', room_id=room_id))  # Перенаправление обратно на страницу кабинета

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    init_db()
    
    app.run(host='0.0.0.0', port = '5000', debug=False)
