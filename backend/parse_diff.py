def parse_diff(patch: str):
    changes = []
    new_line_num = None

    for line in patch.split("\n"):
        # hunk header
        if line.startswith("@@"):
            # @@ -84,3 +84,4 @@ optional context
            part = line.split("+")[1]
            num = part.split(",")[0].split(" ")[0]
            new_line_num = int(num) - 1

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

