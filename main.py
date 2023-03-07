from flask import Flask, render_template_string, url_for
import subprocess
import hashlib
from markupsafe import Markup

app = Flask(__name__)


def jsx(code):
    input_hash = hashlib.new('md5', code.encode('utf-8')).hexdigest()[0:8]
    wrapped_code = f"""
    function Component_{input_hash}() {{
        return <>{code}</>
    }}
    """
    filename = f"out_{input_hash}.js"
    # create the esbuild process
    esbuild_process = subprocess.Popen(['esbuild', '--minify', '--loader=jsx'],
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True)

    # pass input to the esbuild process
    esbuild_output, esbuild_error = esbuild_process.communicate(wrapped_code)
    if esbuild_error:
        print(esbuild_error)
        exit()

    # write esbuild_output to static/filename
    with open(f'static/{filename}', 'w') as f:
        f.write(esbuild_output)

    react_mount = f"""
        {esbuild_output}
        const container = document.getElementById('{input_hash}');
        const root = ReactDOM.createRoot(container);
        root.render(Component_{input_hash}(), );
    """

    script_url = url_for('static', filename=filename)
    injection = f"<div id='{input_hash}'></div><script type='module' src='{script_url}'></script><script type='module'>{react_mount}</script>"
    return Markup(injection)


def render_template_with_react(template):
    return render_template_string(
        '<script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script><script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>{% include "'
        + template + '" %}',
        jsx=jsx)


@app.route('/')
def index():
    return render_template_with_react('home.html')


app.run(host='0.0.0.0', port=81)
