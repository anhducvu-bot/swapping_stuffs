import mysql.connector
import csv
from pathlib import Path

config = {
    'user': 'user',
    'password': 'password',
    'host': '34.86.39.76',
    'database': 'dev-demo',
    'raise_on_warnings': True
}

cnx = mysql.connector.connect(**config)


def populate_user():
    print('Begin USERS')
    cursor = cnx.cursor()
    p = Path(__file__).with_name('users.tsv')
    with p.open() as file:
        tsv_file = csv.reader(file, delimiter="\t")
        first_line = next(tsv_file)
        print(first_line)
        # ['email', 'password', 'first_name', 'last_name', 'nickname', 'postal_code',
        # 'phone_number', 'phone_type', 'to_share']
        for line in tsv_file:
            stmt = """
            INSERT INTO RegularUser (email, password, first_name, last_name, nickname, postal_code)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            args = (line[0:6])
            cursor.execute(stmt, args)

            # Phone Number relation if any
            phone_number = parse_number(line[6])
            if phone_number:
                stmt = """
                INSERT INTO PhoneNumber (email, number, type, share)
                VALUES (%s, %s, %s, %s)
                """
                args = line[0], phone_number, *(line[7:])
                cursor.execute(stmt, args)

    cursor.close()
    cnx.commit()
    print('Finish USERS')
    return


def parse_number(number):
    """
    Parse raw 10 digits number

    :return: XXX-XXX-XXXX
    """
    if len(number) == 10:
        return number[0:3] + '-' + number[3:6] + '-' + number[6:10]
    return ''


def populate_item():
    print('Begin ITEMS')
    cursor = cnx.cursor()
    p = Path(__file__).with_name('items.tsv')
    with p.open() as file:
        tsv_file = csv.reader(file, delimiter="\t")
        first_line = next(tsv_file)
        print(first_line)
        # ['item_number', 'title', 'condition', 'description', 'email', 'type', 'piece_count', 'platform', 'media']
        for line in tsv_file:
            stmt = """
            INSERT INTO Item (title, item_condition, item_description, email, game_type)
            VALUES (%s, %s, %s, %s, %s)
            """
            args = (line[1:6])
            cursor.execute(stmt, args)

            # Child Item tables
            stmt_extra = ""
            args_extra = ""
            game_type = line[5].lower()
            piece_count = line[6]
            platform = line[7]
            media = line[8]
            if game_type == 'video game':
                stmt_extra = """
                INSERT INTO VideoGameItem (item_id, video_game_platform, media)
                VALUES(LAST_INSERT_ID(), %s, %s)
                """
                args_extra = platform, media
            elif game_type == 'computer game':
                stmt_extra = """
                INSERT INTO ComputerGameItem (item_id, computer_platform)
                VALUES (LAST_INSERT_ID(), %s)
                """
                args_extra = platform,
            elif game_type == 'jigsaw puzzle':
                stmt_extra = """
                INSERT INTO JigsawPuzzleItem(item_id, piece_count)
                VALUES (LAST_INSERT_ID(), %s)
                """
                args_extra = piece_count,

            if stmt_extra:
                cursor.execute(stmt_extra, args_extra)

    cursor.close()
    cnx.commit()
    print('Finish ITEMS')
    return


def populate_swap():
    print('Begin SWAPS')
    cursor = cnx.cursor()
    p = Path(__file__).with_name('swaps.tsv')
    with p.open() as file:
        tsv_file = csv.reader(file, delimiter="\t")
        first_line = next(tsv_file)
        print(first_line)
        # ['item_proposed', 'item_desired', 'date_proposed', 'date_reviewed', 'accepted',
        # 'proposer_rate', 'counterparty_rate']
        for line in tsv_file:
            proposed_item = line[0]
            desired_item = line[1]
            extra_swap_info = get_extra_swap_info(proposed_item, desired_item)

            # Swap Details
            stmt = """
            INSERT INTO SwapRequest(proposal_date, completion_date, status, distance)
            VALUES (%s, %s, %s, %s)
            """
            status = adjust_status(line[4])

            args = line[2], adjust_empty_str(line[3]), status, extra_swap_info['distance']
            cursor.execute(stmt, args)

            # Traded items, owners, and roles
            proposer_rating = adjust_empty_str(line[5])
            sql_proposed = """
            INSERT INTO SwapRequestDetail(swap_id, item_id, party, is_proposer, rating)
            VALUES (LAST_INSERT_ID(), %s, %s, True, %s)
            """
            args_proposed = line[0], extra_swap_info['user1'], proposer_rating
            cursor.execute(sql_proposed, args_proposed)

            counterparty_rating = adjust_empty_str(line[6])
            sql_counterparty = """
            INSERT INTO SwapRequestDetail(swap_id, item_id, party, is_proposer, rating)
            VALUES(LAST_INSERT_ID(), %s, %s, False, %s)
            """
            args_counter = line[1], extra_swap_info['user2'], counterparty_rating
            cursor.execute(sql_counterparty, args_counter)

    cursor.close()
    cnx.commit()
    print('Finish SWAPS')
    return


# quite nontrivial and heavy
def get_extra_swap_info(item1, item2):
    sql = """
    WITH
      cte1 AS (
        SELECT latitude AS lat1, longitude as lon1, email as user1
        FROM Item IT1
        NATURAL JOIN RegularUser 
        NATURAL JOIN Address AD1
        WHERE IT1.item_id = %s),
      cte2 AS (
        SELECT latitude AS lat2, longitude as lon2, email as user2
        FROM Item IT2
        NATURAL JOIN RegularUser 
        NATURAL JOIN Address AD2
        WHERE IT2.item_id = %s)
    SELECT user1, user2, haversine(lat1, lon1, lat2, lon2) AS `distance` 
    FROM cte1 JOIN cte2
    """
    cursor = cnx.cursor(dictionary=True)
    cursor.execute(sql, (item1, item2))
    res = cursor.fetchall()[0]
    cursor.close()
    return res


def adjust_status(status_str):
    """
    Adjust raw status data which may be 1, 0, or ''

    :return: 'accepted', 'rejected', or 'pending'
    """
    status = 'ERROR'
    if status_str:
        if status_str == '0':
            status = 'rejected'
        else:
            status = 'accepted'
    else:
        status = 'pending'

    return status


def adjust_empty_str(value):
    """
    '' should be stored as NULL in db
    """
    return value if value else None


if __name__ == '__main__':
    # drop schema and recreate tables first
    populate_user()
    populate_item()
    populate_swap()
    cnx.close()
    print('hi')
