import jinja2
import yaml
import sys
import re

def select_arguments(items):
    arguments = []
    for item in items:
        if not item["name"].startswith("--"):
            arguments.append(item)
    return arguments


def select_parameters(items):
    parameters = []
    for item in items:
        if item["name"].startswith("--"):
            parameters.append(item)
    return parameters


def no_newline(text):
    return re.sub("\n", "", text)


def required(item):
    if "action" in item:
        return False
    elif "default" in item:
        return False
    return True


def data_type_name(item):
    if "action" in item:
        return "marker"
    text = item["type"]
    if text == "str":
        return "string"
    elif text == "int":
        return "integer"
    elif text == "bool":
        return "boolean"
    else:
        return "unknown"


def arg_value(item):
    if "action" in item:
        action = item["action"]
        if action == "store_true" or action == "store_false":
            return ""

    name = item["name"].lower()
    if name.startswith("--"):
        name = name[2:]
    return "=<%s>" % name.replace("-", "_")


def get_description(item):
    if "description" in item:
        return no_newline(item["description"])
    elif "usage" in item:
        return no_newline(item["usage"])
    elif "help" in item:
        return no_newline(item["help"])
    else:
        return "<missing documentation>"


base_path = sys.argv[1]
with open("%s/scripts/sbcli-repo/cli-reference.yaml" % base_path) as stream:
    try:
        reference = yaml.safe_load(stream)

        for command in reference["commands"]:
            for subcommand in command["subcommands"]:
                if "arguments" in subcommand:
                    arguments = select_arguments(subcommand["arguments"])
                    parameters = select_parameters(subcommand["arguments"])
                    subcommand["arguments"] = arguments
                    subcommand["parameters"] = parameters

            templateLoader = jinja2.FileSystemLoader(searchpath="%s/scripts/templates/" % base_path)
            environment = jinja2.Environment(loader=templateLoader)

            environment.filters["no_newline"] = no_newline
            environment.filters["data_type_name"] = data_type_name
            environment.filters["arg_value"] = arg_value
            environment.filters["required"] = required
            environment.filters["get_description"] = get_description

            template = environment.get_template("cli-reference-group.jinja2")
            output = template.render({"command": command})
            with open("%s/docs/reference/cli/%s.md" % (base_path, command["name"]), "t+w") as target:
                target.write(output)

    except yaml.YAMLError as exc:
        print(exc)
