from flask import Flask, request, jsonify, send_file
from math import * # sin, cos, tan, exp, log, sqrt, etc.
import os
import matplotlib
matplotlib.use('Agg') # Use 'Agg' backend for environments without a display server
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

app = Flask(__name__)

def calculate_loan(loan_amount, annual_interest_rate, loan_term_years, interest_type='compound'):
    """
    Calculates the monthly payment, total repayment, and total interest for a loan.
    Args:
        loan_amount (float): The principal loan amount.
        annual_interest_rate (float): The annual interest rate as a percentage.
        loan_term_years (float): The loan term in years.
        interest_type (str): 'simple' or 'compound'. Defaults to 'compound'.
    Returns:
        dict: A dictionary containing 'monthly_payment', 'total_repayment',
              'total_interest', and 'interest_type_calculated',
              or a string error message.
    """
    if not all(isinstance(arg, (int, float)) for arg in [loan_amount, annual_interest_rate, loan_term_years]):
        return "Error: Loan amount, interest rate, and term must be numbers."
    if loan_amount <= 0 or annual_interest_rate < 0 or loan_term_years <= 0:
        return "Error: Loan amount and term must be positive. Interest rate must be non-negative."
    if interest_type not in ['simple', 'compound']:
        return "Error: Invalid interest type. Choose 'simple' or 'compound'."

    total_payments_months = loan_term_years * 12
    monthly_payment = 0
    total_repayment = 0
    total_interest = 0

    try:
        if interest_type == 'simple':
            # Simple Interest Calculation
            # I = P * R * T (where R is annual rate, T is in years)
            rate_decimal = annual_interest_rate / 100
            total_interest = loan_amount * rate_decimal * loan_term_years
            total_repayment = loan_amount + total_interest
            if total_payments_months > 0:
                monthly_payment = total_repayment / total_payments_months
            else: # Should be caught by loan_term_years <= 0 check, but as a safeguard
                return "Error: Loan term in months is zero or negative."

        elif interest_type == 'compound':
            # Compound Interest Calculation (Amortizing Loan Formula)
            if annual_interest_rate == 0: # Edge case: 0% interest
                if total_payments_months > 0:
                    monthly_payment = loan_amount / total_payments_months
                else:
                     return "Error: Loan term in months is zero or negative for 0% interest loan."
                total_repayment = loan_amount
                total_interest = 0
            else:
                monthly_interest_rate = (annual_interest_rate / 100) / 12
                if total_payments_months <= 0:
                    return "Error: Loan term in months is zero or negative."

                # M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1]
                # M = monthly payment, P = principal, i = monthly interest rate, n = number of payments
                if monthly_interest_rate == 0: # Should be covered by annual_interest_rate == 0
                    monthly_payment = loan_amount / total_payments_months
                else:
                    numerator = monthly_interest_rate * (1 + monthly_interest_rate) ** total_payments_months
                    denominator = (1 + monthly_interest_rate) ** total_payments_months - 1
                    if denominator == 0:
                        return "Error: Cannot calculate payment with zero denominator (likely due to extreme values)."
                    monthly_payment = loan_amount * (numerator / denominator)

                total_repayment = monthly_payment * total_payments_months
                total_interest = total_repayment - loan_amount

        return {
            'monthly_payment': round(monthly_payment, 2),
            'total_repayment': round(total_repayment, 2),
            'total_interest': round(total_interest, 2),
            'interest_type_calculated': interest_type
        }
    except OverflowError:
        return "Error: Calculation resulted in an overflow. Please check input values (e.g., very large loan term or interest rate)."
    except Exception as e:
        return f"Error: An unexpected error occurred: {e}"

def perform_calculation(num1, num2, operator): # Removed mode as it was not used
    """Performs a basic arithmetic calculation based on the given operator.

    Args:
        num1 (float): The first number.
        num2 (float): The second number.
        operator (str): The operator (+, -, *, /, ^, root).

    Returns:
        float: The result of the calculation, or an error message string.
    """
    try:
        if operator == '+':
            result = num1 + num2
        elif operator == '-':
            result = num1 - num2
        elif operator == '*':
            result = num1 * num2
        elif operator == '/':
            if num2 == 0:
                return "Error: Division by zero is not allowed."
            result = num1 / num2
        elif operator == '^': # Power
            result = num1 ** num2
        elif operator == 'root': # Nth root
            if num2 == 0:
                return "Error: Cannot take 0th root."
            if num1 < 0 and num2 % 2 == 0: # Even root of a negative number
                 return "Error: Cannot take an even root of a negative number."
            # For fractional roots or negative numbers, ensure correct handling
            if num1 < 0 and num2 % 2 != 0: # Odd root of a negative number
                result = -(-num1)**(1/num2)
            else:
                result = num1 ** (1 / num2)
        else:
            return "Error: Invalid operator. Please use +, -, *, /, ^, or root."
        return result
    except OverflowError:
        return "Error: Calculation resulted in an overflow. Please check input values."
    except Exception as e:
        return f"Error: An unexpected error occurred during calculation: {e}"


@app.route('/', methods=['GET'])
def index():
    """
    Serves the main HTML file.
    """
    # Ensure the path to index.html is correct if it's not in the same directory.
    # For example, if it's in a 'templates' subdirectory:
    # return send_from_directory('templates', 'index.html')
    return send_file('index.html')


@app.route('/calculate', methods=['POST'])
def calculate_route(): # Renamed to avoid conflict with imported calculate function if any
    """
    Handles calculation requests for basic arithmetic, loan calculations, and graph plotting.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    mode = data.get('mode')

    if mode == 'loan':
        loan_amount = data.get('loan_amount')
        annual_interest_rate = data.get('annual_interest_rate')
        loan_term_years = data.get('loan_term_years')
        interest_type = data.get('interest_type', 'compound') # Default to compound if not provided

        # Basic validation for presence of required fields
        if any(arg is None for arg in [loan_amount, annual_interest_rate, loan_term_years]):
            return jsonify({'error': 'Missing loan calculation arguments (loan_amount, annual_interest_rate, loan_term_years).'}), 400

        try:
            loan_amount = float(loan_amount)
            annual_interest_rate = float(annual_interest_rate)
            loan_term_years = float(loan_term_years)
        except ValueError:
            return jsonify({'error': 'Invalid input: Loan parameters must be numbers.'}), 400
        except TypeError: # Handles if None was passed despite the check above
            return jsonify({'error': 'Invalid type for loan parameters.'}), 400


        result = calculate_loan(loan_amount, annual_interest_rate, loan_term_years, interest_type)

        if isinstance(result, str) and result.startswith("Error"):
            return jsonify({'error': result}), 400 # Bad request or server error
        else:
            return jsonify(result), 200

    elif mode == 'basic' or mode == 'currency': # 'currency' mode uses the same basic math
        num1 = data.get('num1')
        num2 = data.get('num2')
        operator = data.get('operator')

        if any(arg is None for arg in [num1, num2, operator]):
            return jsonify({'error': 'Missing basic/currency arguments (num1, num2, operator)'}), 400

        try:
            num1 = float(num1)
            num2 = float(num2)
        except ValueError:
            return jsonify({'error': 'Invalid input: num1 and num2 must be numbers'}), 400
        except TypeError:
            return jsonify({'error': 'Invalid type for num1 or num2.'}), 400


        result = perform_calculation(num1, num2, operator)

        if isinstance(result, str) and result.startswith("Error"):
            return jsonify({'error': result}), 400
        else:
            return jsonify({'result': result}), 200

    elif mode == 'graph':
        expression_str = data.get('expression') # Renamed to avoid conflict
        xmin_val = data.get('xmin', -10)  # default values
        xmax_val = data.get('xmax', 10)
        num_points = data.get('num_points', 400) # Allow customization

        if not expression_str:
            return jsonify({'error': 'Missing expression for graphing.'}), 400

        try:
            xmin = float(xmin_val)
            xmax = float(xmax_val)
            num_points = int(num_points)
            if xmax <= xmin:
                return jsonify({'error': 'xmax must be greater than xmin for graph.'}), 400
            if num_points <= 1:
                return jsonify({'error': 'Number of points for graph must be greater than 1.'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid input for graph range (xmin, xmax) or num_points.'}), 400
        except TypeError:
            return jsonify({'error': 'Invalid type for graph range or num_points.'}), 400


        x_vals = np.linspace(xmin, xmax, num_points)
        y_vals = []

        # Prepare a safe dictionary of allowed functions and constants for eval
        # This is crucial for security to prevent arbitrary code execution.
        safe_dict = {
            "x": 0, # Placeholder, will be updated in loop
            "sin": np.sin, "cos": np.cos, "tan": np.tan,
            "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan,
            "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
            "exp": np.exp, "log": np.log, "log10": np.log10,
            "sqrt": np.sqrt, "abs": np.abs, "pi": np.pi, "e": np.e,
            # Add other safe functions/constants as needed
        }

        try:
            # Replace ^ with ** for Python exponentiation
            processed_expression = expression_str.replace("^","**")
            for val in x_vals:
                safe_dict["x"] = val # Update x value for each point
                y_vals.append(eval(processed_expression, {"__builtins__": {}}, safe_dict))
        except NameError as e: # Catch undefined functions/variables
            return jsonify({'error': f'Error evaluating expression: Undefined name used - {e}. Ensure you use common functions like sin(x), cos(x), exp(x), log(x), sqrt(x) or constants like pi, e.'}), 400
        except SyntaxError as e:
            return jsonify({'error': f'Syntax error in expression: {e}'}), 400
        except TypeError as e: # e.g. math func called with wrong type
            return jsonify({'error': f'Type error in expression (e.g. function called with wrong argument type): {e}'}), 400
        except Exception as e: # Catch-all for other evaluation errors
            return jsonify({'error': f'Error evaluating expression: {e}'}), 400

        # Generate the graph
        plt.figure(figsize=(8, 6)) # Create a new figure for each graph
        plt.plot(x_vals, np.array(y_vals)) # Ensure y_vals is a numpy array for plotting
        plt.xlabel('x')
        plt.ylabel('f(x)')
        plt.title(f'Graph of f(x) = {expression_str}')
        plt.grid(True)
        plt.axhline(0, color='black', lw=0.5) # Add x-axis line
        plt.axvline(0, color='black', lw=0.5) # Add y-axis line

        # Save the graph to a BytesIO object
        img_buf = BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight') # bbox_inches helps prevent cutoff
        img_buf.seek(0)
        plt.close() # Important: Close the figure to free memory

        return send_file(img_buf, mimetype='image/png')

    else:
        return jsonify({'error': 'Invalid mode specified. Valid modes are: loan, basic, currency, graph.'}), 400


if __name__ == "__main__":
    # For development, debug=True is fine. For production, set debug=False.
    # The host '0.0.0.0' makes the server accessible from other devices on the network.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
