import jinja2
import yaml
import sys
import re

def is_parameter(item):
    return item["name"].startswith("--") or item["name"].startswith("-")


def select_arguments(items):
    arguments = []
    for item in items:
        if not is_parameter(item):
            arguments.append(item)
    return arguments


def select_parameters(items):
    parameters = []
    for item in items:
        if is_parameter(item):
            parameters.append(item)
    return parameters


def no_newlines(text):
    return re.sub("\n", "", text)


def trim(text):
    return text.rstrip()


def required(item):
    if "action" in item:
        return False
    elif "default" in item:
        return False
    elif "private" in item and item["private"]:
        return False
    elif "required" in item and item["required"]:
        return True
    elif not item["name"].startswith("--"):
        return True
    return False


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
    name = item["name"].lower()
    if name.startswith("--"):
        raise f"Parameter cannot be used as argument: {name}"
    return f"<{name.replace('-', '_').upper()}>"


def param_value(item):
    if "action" in item:
        action = item["action"]
        if action == "store_true" or action == "store_false":
            return ""

    name = item["name"].lower()
    if name.startswith("--"):
        name = name[2:]
    if name.startswith("-"):
        name = name[1:]
    return f"=<{name.replace('-', '_').upper()}>"


def get_description(item):
    if "description" in item:
        return item["description"]
    elif "usage" in item:
        return no_newlines(item["usage"])
    elif "help" in item:
        return no_newlines(item["help"])
    else:
        return "<missing documentation>"


base_path = sys.argv[1]
with open(f"{base_path}/scripts/sbcli-repo/cli-reference.yaml") as stream:
    try:
        reference = yaml.safe_load(stream)

        for command in reference["commands"]:
            for subcommand in command["subcommands"]:
                if "arguments" in subcommand:
                    arguments = select_arguments(subcommand["arguments"])
                    parameters = select_parameters(subcommand["arguments"])
                    subcommand["arguments"] = arguments
                    subcommand["parameters"] = parameters

            templateLoader = jinja2.FileSystemLoader(searchpath=f"{base_path}/scripts/templates/")
            environment = jinja2.Environment(loader=templateLoader)

            environment.filters["trim"] = trim
            environment.filters["data_type_name"] = data_type_name
            environment.filters["arg_value"] = arg_value
            environment.filters["param_value"] = param_value
            environment.filters["required"] = required
            environment.filters["get_description"] = get_description

            template = environment.get_template("cli-reference-group.jinja2")
            output = template.render({"command": command})
            with open(f"{base_path}/docs/reference/cli/{command['name']}.md", "t+w") as target:
                target.write(output)

    except yaml.YAMLError as exc:
        print(exc)
