from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from datetime import datetime
import json, uuid
app=Flask(__name__)

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
users_table = dynamodb.Table('Users')
orders_table = dynamodb.Table('Orders')

products = {
    'non_veg_pickles': [
        {'id': 1, 'name': 'Chicken Pickle', 'weights': {'250': 600, '500': 1200, '1000': 1800}},
        {'id': 2, 'name': 'Fish Pickle', 'weights': {'250': 200, '500': 400, '1000': 800}},
        {'id': 3, 'name': 'Gongura Mutton', 'weights': {'250': 400, '500': 800, '1000': 1600}},
        {'id': 4, 'name': 'Mutton Pickle', 'weights': {'250': 400, '500': 800, '1000': 1600}},
        {'id': 5, 'name': 'Gongura Prawns', 'weights': {'250': 600, '500': 1200, '1000': 1800}},
        {'id': 6, 'name': 'Chicken Pickle (Gongura)', 'weights': {'250': 350, '500': 700, '1000': 1050}}
    ],
    'veg_pickles': [
        {'id': 7, 'name': 'Traditional Mango Pickle', 'weights': {'250': 150, '500': 280, '1000': 500}},
        {'id': 8, 'name': 'Zesty Lemon Pickle', 'weights': {'250': 120, '500': 220, '1000': 400}},
        {'id': 9, 'name': 'Tomato Pickle', 'weights': {'250': 130, '500': 240, '1000': 450}},
        {'id': 10, 'name': 'Kakarakaya Pickle', 'weights': {'250': 130, '500': 240, '1000': 450}},
        {'id': 11, 'name': 'Chintakaya Pickle', 'weights': {'250': 130, '500': 240, '1000': 450}},
        {'id': 12, 'name': 'Spicy Pandu Mirchi', 'weights': {'250': 130, '500': 240, '1000': 450}}
    ], # Add your veg pickle products here
    'snacks': [
        {'id': 13, 'name': 'Banana Chips', 'weights': {'250': 300, '500': 600, '1000': 800}},
        {'id': 14, 'name': 'Crispy Aam-Papad', 'weights': {'250': 150, '500': 300, '1000': 600}},
        {'id': 15, 'name': 'Crispy Chekka Pakodi', 'weights': {'250': 50, '500': 100, '1000': 200}},
        {'id': 16, 'name': 'Boondhi Acchu', 'weights': {'250': 300, '500': 600, '1000': 900}},
        {'id': 17, 'name': 'Chekkalu', 'weights': {'250': 350, '500': 700, '1000': 1000}},
        {'id': 18, 'name': 'Ragi Laddu', 'weights': {'250': 350, '500': 700, '1000': 1000}},
        {'id': 19, 'name': 'Dry Fruit Laddu', 'weights': {'250': 500, '500': 1000, '1000': 1500}},
        {'id': 20, 'name': 'Kara Boondi', 'weights': {'250': 250, '500': 500, '1000': 750}},
        {'id': 21, 'name': 'Gavvalu', 'weights': {'250': 250, '500': 500, '1000': 750}},
        {'id': 22, 'name': 'Kaju Chikki', 'weights': {'250': 250, '500': 500, '1000': 750}}
    ]
}
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            response = users_table.get_item(Key={'username': username})
            if 'Item' not in response:
                return render_template('login.html', error="User not found")

            user = response['Item']
            if check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['username'] = username
                session.setdefault('home', [])
                return redirect(url_for('home'))  # ✅ Add this to redirect after login
            else:
                return render_template('login.html', error="Incorrect password")
        except Exception as e:
            return render_template('login.html', error=f"An error occurred: {str(e)}")
    
    # ✅ This was missing
    return render_template('login.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email =request.form['email'].strip()
        password= request.form['password']
        try:
            response = users_table.get_item(Key={'username': username})
            if 'Item' in response:
                return render_template('signup.html', error = 'Username already exists')
            
            hashed_password = generate_password_hash(password)

            users_table.put_item(
                Item={
                    'username': username,
                    'email': email,
                    'password': hashed_password,
                }
            )

            return redirect(url_for('login'))

        except Exception as e:
            app.logger.error(f"Signup error: {str(e)}")
            return render_template('signup.html', error='Registration failed. Please try again.')
    return render_template('signup.html')

@app.route('/logout')
def logout():
        session.clear()
        return redirect(url_for('login'))

@app.route('/home')
def home():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return render_template('home.html')

@app.route('/non_veg_pickles')
def non_veg_pickles():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('non_veg_pickles.html', products=products ['non_veg_pickles'])

@app.route('/veg_pickles')
def veg_pickles():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
   
    # Simply pass all products without filtering
    return render_template('veg_pickles.html', products=products ['veg_pickles'])                                                               

@app.route('/snacks')
def snacks():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('snacks.html', products=products['snacks'])
                
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    error_message = None # Variable to hold error messages
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            address = request.form.get('address', '').strip()
            phone = request.form.get('phone', '').strip()
            payment_method = request.form.get('payment', '').strip()
            #Validate inputs
            if not all([name, address, phone, payment_method]):
                return render_template('checkout.html', error="All fields are required.")
            
            if not phone.isdigit() or len(phone) != 10:
                return render_template('checkout.html', error="Phone number must be exactly 10 digits.")
            #Get cart data from hidden inputs
            cart_data = request.form.get('cart_data', '[]')
            total_amount = request.form.get('total_amount', '0')
            try:
                cart_items = json.loads(cart_data)
                total_amount = float(total_amount)
            except (json.JSONDecodeError, ValueError):
                return render_template('checkout.html', error="Invalid cart data format.")
            # Ensure cart is not empty
            if not cart_items:
                return render_template('checkout.html', error="Your cart is empty.")
            try:
                orders_table.put_item(
                    Item={
                        'order_id': str(uuid.uuid4()),
                        'username': session.get('username', 'Guest'),
                        'name': name,
                        'address': address,
                        'phone': phone,
                        'items': cart_items,
                        'total_amount': total_amount,
                        'payment_method': payment_method,
                        'timestamp': datetime.now().isoformat()
                    }
                )
            except Exception as db_error:
                print(f"DynamoDB Error: {db_error}")
                return render_template('checkout.html', error="Failed to save order. Please try again later.")
            # Redirect to success page with success message
            return redirect(url_for('sucess', message="Your order has been placed successfully!"))
        except Exception as e:
            print(f"Checkout error: {str(e)}")
            return render_template('checkout.html', error="An unexpected error occurred. Please try again.")
    return render_template('checkout.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/sucess')
def success():
    return render_template('sucess.html')

@app.route('/about')
def about():
    return render_template('about.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # Add debug True temporarily

            