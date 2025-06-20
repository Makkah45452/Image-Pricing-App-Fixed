from flask import Flask, request, render_template, redirect, url_for, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

product_data = []
current_index = 0
skipped_indices = set()
view_mode = 'all'

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    global product_data, current_index, skipped_indices, view_mode
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
            file.save(filepath)
            df = pd.read_excel(filepath)[['SKU', 'ZSKU', 'TITLE', 'IMAGE-URLS']]
            df['Price'] = None
            product_data = df.to_dict('records')
            current_index = 0
            skipped_indices = set()
            view_mode = 'all'
            return redirect(url_for('entry'))
    return render_template('upload.html')

@app.route('/entry', methods=['GET', 'POST'])
@app.route('/toggle_view/<mode>', methods=['GET'])
def entry(mode=None):
    global product_data, current_index, skipped_indices, view_mode

    if request.method == 'GET' and mode:
        view_mode = mode
        current_index = 0
        return redirect(url_for('entry'))

    # Determine the current list of items based on view_mode
    if view_mode == 'all':
        items = [i for i in range(len(product_data))]
    elif view_mode == 'skipped':
        items = [i for i in range(len(product_data)) if not product_data[i]['Price']]
    else:
        items = []

    if request.method == 'POST':
        if current_index < len(items):
            real_index = items[current_index]
            action = request.form.get('action')
            price = request.form.get('price')

            if action == 'save' and price:
                product_data[real_index]['Price'] = price
                skipped_indices.discard(real_index)
            elif action == 'skip':
                skipped_indices.add(real_index)
            elif action == 'back':
                current_index = max(0, current_index - 1)
                return redirect(url_for('entry'))

            if current_index < len(items) - 1:
                current_index += 1
            else:
                current_index += 1

        return redirect(url_for('entry'))

    if current_index < len(items):
        real_index = items[current_index]
        item = product_data[real_index]
        filled_count = sum(1 for p in product_data if p['Price'])
        skipped_count = sum(1 for p in product_data if not p['Price'])
        return render_template('entry.html', item=item, index=current_index + 1, current=real_index,
                               total=len(items), filled=filled_count, skipped=skipped_count, view=view_mode)

    return redirect(url_for('complete'))

@app.route('/complete')
def complete():
    skipped_count = sum(1 for p in product_data if not p['Price'])
    return render_template('complete.html', skipped=skipped_count)

@app.route('/export')
def export():
    df = pd.DataFrame(product_data)
    output_path = os.path.join(UPLOAD_FOLDER, 'priced_output.csv')
    df.to_csv(output_path, index=False)
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
