from flask import Blueprint, render_template, redirect

from app.models import EditableHTML, Department, ContrType

from app.main.forms import ResultsForm

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
@main.route('/search', methods=['GET', 'POST'])
def search():
    form = ResultsForm()
    depts = Department.query.all()
    types = ContrType.query.all()
    if form.validate():
        return redirect('results')
    return render_template('main/search.html', depts = depts, types = types, form = form)

# Route to results page, where results of city contracts searching appear
@main.route('/results', methods=['GET', 'POST'])
def results():
    return render_template('main/results.html')


# Route to contact page, where users can contact City Controller's Office
@main.route('/contact')
def contact():
    return render_template('main/contact.html')
