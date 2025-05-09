from flask import Flask, request, jsonify, send_file
from math import *
import os

app = Flask(__name__)

def perform_calculation(num1, num2, operator, mode='basic'):
    """
    Performs a calculation based on the given numbers, operator, and mode.
    Args:
        num1 (float): The first number.
        num2 (float): The second number.
        operator (str): The operator (+, -, *, /, %, ^, sqrt, log, convert).
        mode (str, optional): The calculator mode ('basic', 'currency'). Defaults to 'basic'.
    Returns:
        float: The result of the calculation, or an error message.
    """
    try:
        if mode == 'basic':
            if operator == '+':
                return num1 + num2
            elif operator == '-':
                return num1 - num2
            elif operator == '*':
                return num1 * num2
            elif operator == '/':
                if num2 == 0:
                    return "Error: Division by zero"
                return num1 / num2
            elif operator == '%':
                if num2 == 0:
                    return "Error: Division by zero"
                return num1 % num2
            elif operator == '^':
                return num1 ** num2
            elif operator == 'sqrt':
                if num2 < 0:
                    return "Error: Square root of a negative number"
                return num2 ** 0.5
            elif operator == 'log':
                if num1 <= 0 or num2 <= 0:
                    return "Error: Logarithm of non-positive number"
                return log(num2, num1)  # Log base num1 of num2
            else:
                return "Error: Invalid operator for basic mode"
        elif mode == 'currency':
            # Placeholder for currency conversion logic
            # In a real application, you would use an API or a database
            # to get the exchange rate and perform the conversion.
            if operator == 'convert':
                if num1 == 0:
                    return "Error: Invalid exchange rate"
                return num2 * num1  # num1 is the exchange rate, num2 is the amount
            else:
                return "Error: Invalid operator for currency mode.  Use 'convert'"
        else:
            return "Error: Invalid mode"
    except Exception as e:
        return f"Error: {e}"

@app.route('/', methods=['GET', 'POST'])
def calculate():
    """
    Handles the main endpoint for performing calculations.
    Accepts GET to serve the calculator, and POST to perform calculations.
    """
    if request.method == 'GET':
        # Serve the index.html file from the root directory
        return send_file('index.html')
    elif request.method == 'POST':
        data = request.get_json()
        num1 = data.get('num1')
        num2 = data.get('num2')
        operator = data.get('operator')
        mode = data.get('mode', 'basic')

        if any(arg is None for arg in [num1, num2, operator]):
            return jsonify({'error': 'Missing arguments'}), 400

        result = perform_calculation(num1, num2, operator, mode)
        if isinstance(result, str) and result.startswith("Error"):
            return jsonify({'error': result}), 400
        else:
            return jsonify({'result': result}), 200

if __name__ == "__main__":
    app.run(debug=True)
