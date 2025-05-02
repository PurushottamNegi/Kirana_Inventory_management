from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'inventory.csv')

# Initialize inventory CSV if not exists
if not os.path.exists(DATA_FILE):
    data = {
        'Item': ['Rice', 'Atta', 'Dal', 'Sugar', 'Oil', 'Spices', 'Tea', 'Biscuits'],
        'Quantity': [100, 80, 50, 60, 30, 100, 50, 120],
        'Price': [60, 40, 120, 45, 180, 30, 80, 20],
        'Unit': ['kg', 'kg', 'kg', 'kg', 'liter', 'pkt', 'pkt', 'pkt']
    }
    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False)

def load_inventory():
    return pd.read_csv(DATA_FILE)

def save_inventory(df):
    df.to_csv(DATA_FILE, index=False)

@app.route('/')
def index():
    inventory = load_inventory()
    low_stock_items = inventory[inventory['Quantity'] < 20]['Item'].tolist()
    return render_template('index.html', inventory=inventory.to_dict(orient='records'), low_stock_items=low_stock_items)

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    item = request.form.get('item')
    quantity_str = request.form.get('quantity', '0')
    try:
        quantity = int(quantity_str)
    except ValueError:
        flash("Quantity must be an integer.", "danger")
        return redirect(url_for('index'))
    df = load_inventory()
    if item in df['Item'].values:
        index = df.index[df['Item'] == item][0]
        if df.at[index, 'Quantity'] >= quantity:
            df.at[index, 'Quantity'] -= quantity
            save_inventory(df)
            flash(f"{quantity} {item} sold.", "success")
        else:
            flash(f"Not enough {item} in stock.", "danger")
    else:
        flash(f"{item} not found in inventory.", "danger")
    return redirect(url_for('index'))

@app.route('/generate_bill', methods=['POST'])
def generate_bill():
    items = request.form.getlist('bill_item')
    quantities = request.form.getlist('bill_quantity')
    df = load_inventory()
    bill_items = []
    total_bill = 0
    for item, qty_str in zip(items, quantities):
        quantity = int(qty_str) if qty_str.isdigit() else 0
        if item in df['Item'].values:
            index = df.index[df['Item'] == item][0]
            price = df.at[index, 'Price']
            cost = price * quantity
            bill_items.append({'item': item, 'quantity': quantity, 'cost': cost})
            total_bill += cost
        else:
            flash(f"{item} not found in inventory.", "error")
    return render_template('bill.html', bill_items=bill_items, total=total_bill)

# Additional features start here

@app.route('/add_item', methods=['POST'])
def add_item():
    item = request.form.get('new_item')
    quantity = request.form.get('new_quantity')
    price = request.form.get('new_price')
    unit = request.form.get('new_unit')
    if not item or not quantity or not price or not unit:
        flash("Please provide item name, quantity, price, and unit.", "danger")
        return redirect(url_for('index'))
    try:
        quantity = int(quantity)
        price = float(price)
    except ValueError:
        flash("Quantity must be an integer and price must be a number.", "danger")
        return redirect(url_for('index'))
    df = load_inventory()
    if item in df['Item'].values:
        flash("Item already exists. Use update price or update inventory.", "danger")
        return redirect(url_for('index'))
    new_row = {'Item': item, 'Quantity': quantity, 'Price': price, 'Unit': unit}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_inventory(df)
    flash(f"Item {item} added successfully.", "success")
    return redirect(url_for('index'))

@app.route('/update_price', methods=['POST'])
def update_price():
    item = request.form.get('price_item')
    new_price = request.form.get('new_price_value')
    if not item or not new_price:
        flash("Please provide item and new price.", "danger")
        return redirect(url_for('index'))
    try:
        new_price = float(new_price)
    except ValueError:
        flash("Price must be a number.", "danger")
        return redirect(url_for('index'))
    df = load_inventory()
    if item in df['Item'].values:
        index = df.index[df['Item'] == item][0]
        df.at[index, 'Price'] = new_price
        save_inventory(df)
        flash(f"Price for {item} updated to {new_price}.", "success")
    else:
        flash(f"{item} not found in inventory.", "danger")
    return redirect(url_for('index'))

@app.route('/edit_item_name', methods=['POST'])
def edit_item_name():
    old_name = request.form.get('old_item_name')
    new_name = request.form.get('new_item_name')
    if not old_name or not new_name:
        flash("Please provide both old and new item names.", "danger")
        return redirect(url_for('index'))
    df = load_inventory()
    if old_name not in df['Item'].values:
        flash(f"Item '{old_name}' not found in inventory.", "danger")
        return redirect(url_for('index'))
    if new_name in df['Item'].values:
        flash(f"Item name '{new_name}' already exists. Choose a different name.", "danger")
        return redirect(url_for('index'))
    index = df.index[df['Item'] == old_name][0]
    df.at[index, 'Item'] = new_name
    save_inventory(df)
    flash(f"Item name changed from '{old_name}' to '{new_name}'.", "success")
    return redirect(url_for('index'))

@app.route('/delete_item', methods=['POST'])
def delete_item():
    item = request.form.get('delete_item_name')
    if not item:
        flash("Please select an item to delete.", "danger")
        return redirect(url_for('index'))
    df = load_inventory()
    if item in df['Item'].values:
        df = df[df['Item'] != item]
        save_inventory(df)
        flash(f"Item '{item}' deleted successfully.", "success")
    else:
        flash(f"Item '{item}' not found in inventory.", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
