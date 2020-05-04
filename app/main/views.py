from flask import Blueprint, render_template

from app.models import EditableHTML

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('main/index.html')


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)

# Route to search page, where users can search for city contracts
@main.route('/search')
def search():
    return render_template('main/search.html')

# Route to contact page, where users can contact City Controller's Office
@main.route('/contact')
def contact():
    return render_template('main/contact.html')

# Route to tips page, where users can find search tips
@main.route('/tips')
def tips():
    return render_template('main/tips.html')

# Route to report page, where users can report page
@main.route('/report')
def report():
    return render_template('main/report.html')