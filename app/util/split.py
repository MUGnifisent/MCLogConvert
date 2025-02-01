def split_on_second_space(s: str) -> list:
    # Find the position of the first space
    first_space = s.find(' ')
    # Find the position of the second space, starting the search after the first space
    second_space = s.find(' ', first_space + 1)
    
    # If there is no second space, return the original string as the first part
    if second_space == -1:
        return [s, '']
    
    # Split the string at the second space
    part1 = s[:second_space]
    part2 = s[second_space + 1:]
    return [part1, part2]