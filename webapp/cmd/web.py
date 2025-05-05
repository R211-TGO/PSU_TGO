from webapp.web import create_app, get_program_options


def main():
    app = create_app()
    options = get_program_options()
    app.run(host=options.host, port=int(options.port), debug=options.debug)
