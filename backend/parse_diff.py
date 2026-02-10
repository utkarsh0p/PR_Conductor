def parse_diff(patch: str):
    changes = []
    new_line_num = None

    for line in patch.split("\n"):
        # hunk header
        if line.startswith("@@"):
            # @@ -84,3 +84,4 @@
            new_line_num = int(line.split("+")[1].split(",")[0]) - 1

        elif line.startswith("+") and not line.startswith("+++"):
            new_line_num += 1
            changes.append({
                "line": new_line_num,
                "code": line[1:]
            })

        elif not line.startswith("-"):
            if new_line_num is not None:
                new_line_num += 1

    return changes

