# -*- coding: utf-8 -*-
import boto3
import json
import os
import argparse


def build_service_sheet(exclude_services=None):
    session = boto3.Session()

    all_services = []

    if exclude_services is None:
        exclude_services = []

    for service_name in session.get_available_services():
        if service_name in exclude_services:
            continue

        client = session.client(service_name)
        methods = [
            method
            for method in dir(client)
            if callable(getattr(client, method))
            and method.startswith(("get", "describe", "list"))
        ]

        service_sheet = []

        scan_dir = os.path.join("scan", "sample", "services")
        # Ensure the directory exists
        os.makedirs(scan_dir, exist_ok=True)

        for method in methods:
            function_data = {"service": service_name, "function": method}

            parameters = {}

            # Add paginator and waiter information
            if method not in ("get_paginator", "get_waiter"):
                if client.can_paginate(method):
                    paginator = client.get_paginator(method)
                    actual_operation_name = client._PY_TO_OP_NAME.get(method)
                    if actual_operation_name:
                        paginator_config = client._cache['page_config'].get(actual_operation_name)
                        if paginator_config:
                            function_data["paginator"] = method
                            function_data["config"] = paginator_config
                        else:
                            function_data["paginator"] = method
                        parameters["operation_name"] = method
                    else:
                        function_data["paginator"] = method
                        parameters["operation_name"] = method

            #if parameters:
            #    function_data["parameters"] = parameters
            service_sheet.append(function_data)

            # TBD: Are there waiters we need? These are for pending ops
            # like deleting a bucket or creating a cert, etc.
            # but we expect all resources to be available for inventory
            # Add waiter information
            #waiter_names = client.waiter_names
            #if waiter_names:
            #    for waiter_name in waiter_names:
            #        waiter_data = {"service": service_name, "function": method}
            #        waiter_data["parameters"] = {"waiter_name": f"{waiter_name}"}
            #        service_sheet.append(waiter_data)

        with open(os.path.join(scan_dir, f"{service_name}.json"), "w") as f:
            json.dump(service_sheet, f)

        all_services.append(service_sheet)

    # Flatten the list of lists into a single list
    all_services_flat = [item for sublist in all_services for item in sublist]

    with open(os.path.join(scan_dir, "all_services.json"), "w") as f:
        json.dump(all_services_flat, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build service sheets for AWS services.")
    parser.add_argument("--exclude-services", type=str, help="Comma-separated list of services to exclude.")
    args = parser.parse_args()

    exclude_services = []
    if args.exclude_services:
        exclude_services = args.exclude_services.split(",")

    build_service_sheet(exclude_services=exclude_services)
