from MySQLdb import cursors
from app_config import mysql, logger
from datetime import datetime


def execute(statement, args=None):
    """
    Execute a single query and fetch the result

    :param statement: the query
    :param args: optional parameters to use in the query. If tuple, use '%s'. If dict, use '%(key)s'

    :return: a list of rows as dicts where keys are column names, or an empty list
    """
    cur = mysql.connection.cursor(cursorclass=cursors.DictCursor)
    res = []
    try:
        cur.execute(statement, args)
        mysql.connection.commit()
        res = cur.fetchall()
    except Exception as e:
        cur.close()
        logger.exception(e)
        raise e
    cur.close()
    return res


def get_user_info(user_id):
    sql = """
        SELECT *, IF(share, True, False) AS share_phone
        FROM RegularUser ru 
        LEFT OUTER JOIN PhoneNumber pn on ru.email = pn.email 
        LEFT OUTER JOIN Address ad on ru.postal_code = ad.postal_code
        WHERE ru.email= %s;
  """
    args = user_id,
    res = execute(sql, args)[0]
    return res


def get_user_full_name(user_id):
    sql = """
      SELECT first_name, last_name 
      FROM RegularUser 
      WHERE email=%s
  """
    args = user_id,
    res = execute(sql, args)[0]
    fullName = res['first_name'] + " " + res['last_name']
    return fullName


def get_rating(user_id):
    sql = """
        SELECT IFNULL(ROUND(AVG(rating), 2), 'None') AS rating
        FROM
            SwapRequestDetail
        WHERE party = %s
        """
    args = user_id,
    res = execute(sql, args)[0]['rating']
    return res


def get_num_pending_swaps(user_id):
    sql = """
        SELECT count(*)
        FROM SwapRequest NATURAL JOIN SwapRequestDetail
        WHERE status='pending'
        AND party=%s
        AND is_proposer=0
    """
    args = user_id,
    res = execute(sql, args)[0]['count(*)']
    return res

def get_num_pending_swaps_profile(user_id):
    sql = """
        SELECT count(*)
        FROM SwapRequest NATURAL JOIN SwapRequestDetail
        WHERE status='pending'
        AND party=%s
    """
    args = user_id,
    res = execute(sql, args)[0]['count(*)']
    return res

# FUNCTION DEPRECATED - USE len(get_unrated_swap_list()) instead
# def get_num_unrated_swaps(user_id):
#     sql = """
#         SELECT count(*)
#         FROM SwapRequest NATURAL JOIN SwapRequestDetail
#         WHERE status='accepted'
#         AND party=%s
#         AND rating IS NULL
#     """
#     args = user_id,
#     res = execute(sql, args)[0]['count(*)']
#     return res


def get_my_items(user_id):
    #CONCAT(LEFT(item_description, 100), "...") to concate ... at the end
    sql = """
        SELECT item_id, title, item_condition, item_description, game_type
        FROM Item 
        WHERE email=%s AND (item_id NOT IN (
		    SELECT SwapRequestDetail.item_id
		    FROM SwapRequestDetail
			INNER JOIN SwapRequest
			ON SwapRequestDetail.swap_id = SwapRequest.swap_id
			WHERE (status = "pending" OR status = "accepted")
        ))
        ORDER BY item_id;
    """
    args = user_id,
    res = execute(sql, args)

    # print("row: ", res)
    if len(res) == 0:
        return []
    else:
        result = res
        #print("result: ", result)
        #print("type of result: ", type(result))
        return result


def get_my_item_counts(user_id):
    res = get_my_items(user_id)
    # print("get_my_item_counts res: ", res)
    counts = {'num_board_games': 0,
              'num_card_games': 0,
              'num_computer_games': 0,
              'num_jigsaw_puzzles': 0,
              'num_video_games': 0,
              'total_num_games': 0}

    if res:
        for row in res:
            # print("row: ", row)
            if row['game_type'].lower() == 'board game':
                counts['num_board_games'] += 1
            elif row['game_type'].lower() == 'card game':
                counts['num_card_games'] += 1
            elif row['game_type'].lower() == 'computer game':
                counts['num_computer_games'] += 1
            elif row['game_type'].lower() == 'jigsaw puzzle':
                counts['num_jigsaw_puzzles'] += 1
            elif row['game_type'].lower() == 'video game':
                counts['num_video_games'] += 1
        counts['total_num_games'] = len(res)
        #print("game type counts: ", counts)

    return counts


def get_user_available_items(user_id, desired_item_id):
    sql = """
        SELECT item_id, game_type, title, item_condition
        FROM Item
        WHERE email=%s
        AND item_id NOT IN (
        SELECT item_id
        FROM SwapRequest NATURAL JOIN SwapRequestDetail
        WHERE status IN ('pending', 'accepted')
        )
        AND item_id NOT IN (
        SELECT SRD2.item_id
        FROM SwapRequest AS SR JOIN SwapRequestDetail AS SRD
        ON SR.swap_id = SRD.swap_id
        JOIN SwapRequestDetail AS SRD2
        ON SRD.swap_id = SRD2.swap_id
        WHERE SRD.item_id = %s AND SR.status = 'rejected'
        AND SRD2.item_id <> %s
        )
        ORDER BY item_id
    """
    args = user_id, desired_item_id, desired_item_id
    res = execute(sql, args)
    return res


def propose_swap(distance, desired_item_id, counter_party_email, proposed_item_id, proposer_email):
    sr_sql = """
      INSERT INTO SwapRequest(proposal_date, status, distance)
      VALUES (CURDATE(), 'pending', %s)
  """
    sr_args = distance,
    execute(sr_sql, sr_args)

    id_sql = "SELECT LAST_INSERT_ID()"
    res = execute(id_sql)
    swap_id = res[0]['LAST_INSERT_ID()']

    cp_srd_sql = """
      INSERT INTO SwapRequestDetail(swap_id, item_id, party, is_proposer)
      VALUES (%s, %s, %s, 0)
  """
    cp_srd_args = swap_id, desired_item_id, counter_party_email,
    execute(cp_srd_sql, cp_srd_args)

    p_srd_sql = """
      INSERT INTO SwapRequestDetail(swap_id, item_id, party, is_proposer)
      VALUES (%s, %s, %s, 1)
  """
    p_srd_args = swap_id, proposed_item_id, proposer_email,
    execute(p_srd_sql, p_srd_args)


def get_swap_history(user_id):
    """
    Find all swap details including info about current user, counterparty,
    traded items, ratings
    """
    sql = """
        SELECT SR.swap_id, status, proposal_date, distance, SR.completion_date, SD.is_proposer, 
        IT.title AS `my_item`, IT_OTHER.title AS `their_item`, 
        RU_OTHER.nickname AS `other_user_name`, 
        RU.email AS `current_user`, RU_OTHER.email AS `other_user`,
        SD.rating AS `my_rating`,
        SD_OTHER.rating AS `their_rating`,
        getRating(SD_OTHER.party) AS `their_avg_rating`
        FROM SwapRequest SR 
        JOIN SwapRequestDetail SD  ON SD.swap_id = SR.swap_id
        JOIN SwapRequestDetail SD_OTHER ON SD.swap_id = SD_OTHER.swap_id 
        AND SD_OTHER.party <> %s
        JOIN Item IT ON SD.item_id = IT.item_id
        JOIN Item IT_OTHER ON SD_OTHER.item_id = IT_OTHER.item_id
        JOIN RegularUser RU ON SD.party = RU.email
        JOIN RegularUser RU_OTHER ON SD_OTHER.party = RU_OTHER.email
        WHERE SD.party = %s
        ORDER BY completion_date DESC, proposal_date ASC;
    """
    args = user_id, user_id
    res = execute(sql, args)
    for row in res:
        if row['is_proposer']:
            row['desired_item'] = row['their_item']
            row['proposed_item'] = row['my_item']
        else:
            row['desired_item'] = row['my_item']
            row['proposed_item'] = row['their_item']
    return res


def get_completed_swap_list(user_id):
    res = get_swap_history(user_id)
    completed_res = []
    completed_status = 'accepted', 'rejected'
    for row in res:
        if row['status'].lower() in completed_status:
            completed_res.append(row)
    return completed_res


def get_pending_proposed_swap(user_id):
    """
    Find pending swaps proposed to this user
    """
    res = get_swap_history(user_id)
    pending_res = []
    for row in res:
        if row['status'].lower() == 'pending' and not row['is_proposer']:
            pending_res.append(row)
    return pending_res


def get_unrated_swap_list(user_id):
    res = get_swap_history(user_id)
    unrated_res = []
    for row in res:
        if row['status'].lower() == 'accepted' and row['their_rating'] is None:
            unrated_res.append(row)
    return unrated_res


def has_old_unrated_swap(user_id):
    unrated_swaps = get_unrated_swap_list(user_id)

    for row in unrated_swaps:
        if is_date_older_than(row['proposal_date'], 5):
            return True
    return False


def has_old_pending_swap(user_id):
    swaps = get_pending_proposed_swap(user_id)

    for row in swaps:
        if is_date_older_than(row['proposal_date'], 5):
            return True
    return False


def is_date_older_than(date, no_of_days):
    return (date.today() - date).days > 5


def get_swap_summary(user_id):
    sql = """
        SELECT is_proposer, status, COUNT(*) AS `count`
        FROM SwapRequest SR JOIN SwapRequestDetail SD
        ON SR.swap_id = SD.swap_id
        WHERE SD.party = %s AND status <> 'pending'
        GROUP BY is_proposer, status
    """
    args = user_id,
    raw = execute(sql, args)

    """
    Transpose
        True | Accepted | 1
        True | Rejected | 1
        False| Accepted | 1
    To 
        True | Accepted = 1 | Rejected = 1
        False| Accepted = 1 | Rejected = 0
    """
    summary = {True: {"role": 'proposer', 'total': 0, 'accepted': 0, 'rejected': 0, 'pending': 0},
               False: {"role": 'counterparty', 'total': 0, 'accepted': 0, 'rejected': 0, 'pending': 0}}
    for row in raw:
        is_proposer = row['is_proposer']
        summary[is_proposer][row['status']] += row['count']
        summary[is_proposer]['total'] += row['count']
    for key, value in summary.items():
        value['percent_reject'] = 0
        if value['total'] != 0:
            value['percent_reject'] = 100 * (value['rejected'] / value['total'])

    return list(summary.values())


def set_rating(swap_id, rater, rating):
    sql = """
        UPDATE SwapRequestDetail
        SET rating = %s
        WHERE swap_id = %s AND party <> %s
    """
    args = rating, swap_id, rater
    return execute(sql, args)


def set_swap_status(swap_id, status):
    sql = """
    UPDATE SwapRequest SET status = %s
    WHERE swap_id = %s
    """
    args = status.lower(), swap_id
    return execute(sql, args)


def create_item(data):
    sql = """
        INSERT INTO Item(email, item_description, title, item_condition, game_type)
        VALUES (%(email)s, %(description)s, %(title)s, %(condition)s, %(gameTypeDropdown)s);
    """
    args = data
    execute(sql, args)

    if data["gameTypeDropdown"].lower() == "video game":
        sql2 = """
            INSERT INTO VideoGameItem(item_id, video_game_platform, media)
            VALUES (LAST_INSERT_ID(), %(platform)s, %(media1)s);
        """
        execute(sql2, args)

    elif data["gameTypeDropdown"].lower() == "computer game":
        sql2 = """
            INSERT INTO ComputerGameItem(item_id, computer_platform)
            VALUES (LAST_INSERT_ID(), %(media)s);
        """
        execute(sql2, args)
    elif data["gameTypeDropdown"].lower() == "jigsaw puzzle":
        sql2 = """
            INSERT INTO JigsawPuzzleItem(item_id, piece_count)
            VALUES (LAST_INSERT_ID(), %(pieceCount)s);
        """
        execute(sql2, args)


def get_item_detail(item_id):
    sql = """
        SELECT A.*, B.video_game_platform, B.media,  
        C.piece_count, D.computer_platform 	 
        FROM Item A
        LEFT JOIN VideoGameItem B ON A.item_id = B.item_id 
        LEFT JOIN JigsawPuzzleItem C ON A.item_id = C.item_id 
        LEFT JOIN ComputerGameItem D ON	A.item_id = D.item_id  
        WHERE A.item_id = %s; 
    """
    args = item_id,
    return execute(sql, args)[0]


def get_user_detail(user_id):
    sql = """
        SELECT *, IF(share, True, False) AS share_phone
        FROM RegularUser RU 
        LEFT JOIN PhoneNumber PN
        ON RU.email = PN.email
        WHERE RU.email = %s
    """
    return execute(sql, (user_id,))[0]


def get_swap_detail(current_user, swap_id):
    data = {}
    swap_detail = {}
    current_user_info = {}
    other_user_info = {}
    proposed_item = {}
    desired_item = {}
    # Swap details
    sql0 = """
        SELECT * FROM SwapRequest SR WHERE SR.swap_id = %s
    """
    swap_detail = execute(sql0, (swap_id,))[0]
    # Item details
    sql1 = """
        SELECT * FROM SwapRequest SR 
        JOIN SwapRequestDetail SD ON SR.swap_id = SD.swap_id
        WHERE SR.swap_id = %s
    """
    swaps = execute(sql1, (swap_id,))
    # User details
    for row in swaps:
        if row['is_proposer']:
            proposed_item = get_item_detail(row['item_id'])
        else:
            desired_item = get_item_detail(row['item_id'])
        if row['party'] == current_user:
            current_user_info = get_user_detail(row['party'])
            current_user_info['rating'] = row['rating']
        else:
            other_user_info = get_user_detail(row['party'])
            other_user_info['rating'] = row['rating']
    data['swap_detail'] = swap_detail
    data['current_user'] = current_user_info
    data['other_user'] = other_user_info
    data['proposed_item'] = proposed_item
    data['desired_item'] = desired_item
    return data


# Search Function
def all_available_item(user_id):
    """
    Find all available item for search function
    """
    sql = """
    SELECT item_id, RU.email, game_type,title, item_condition, item_description, RU.postal_code, longitude, latitude
    FROM Item
        JOIN RegularUser RU ON Item.email = RU.email
    JOIN Address ON Address.postal_code = RU.postal_code
    WHERE RU.email <> %s
    AND item_id NOT IN
    (SELECT item_id as itemz
    FROM SwapRequest
    JOIN SwapRequestDetail ON SwapRequestDetail.swap_id=SwapRequest.swap_id
    WHERE SwapRequest.status = 'pending' OR SwapRequest.status = 'accepted')
    """
    args = user_id,
    return execute(sql, args)


def user_postal_code(user_id):
    '''
    Query current user postal code
    '''

    sql = """
    SELECT postal_code from RegularUser
    WHERE email = %s
    """
    args = user_id,
    return execute(sql, args)


def search_by_keyword(user_id, key_word):
    key_word = "%" + key_word + "%"
    sql = """
    WITH search_by_keyword AS (
    SELECT item_id, RU.email, game_type,title, item_condition, item_description, RU.postal_code, longitude, latitude
    FROM Item
        JOIN RegularUser RU ON Item.email = RU.email
    JOIN Address ON Address.postal_code = RU.postal_code
    WHERE RU.email <> %s and (title LIKE %s OR item_description LIKE %s)
    AND item_id NOT IN
    (SELECT item_id as itemz
    FROM SwapRequest
    JOIN SwapRequestDetail ON SwapRequestDetail.swap_id=SwapRequest.swap_id
    WHERE SwapRequest.status = 'pending' OR SwapRequest.status = 'accepted')
    )
    SELECT search_by_keyword.email,search_by_keyword.item_id,search_by_keyword.game_type,search_by_keyword.title,search_by_keyword.item_condition,search_by_keyword.item_description, ROUND(haversine(Address.latitude, Address.longitude, search_by_keyword.latitude, search_by_keyword.longitude), 2) AS `distance` 
    FROM RegularUser RU JOIN Address 
    CROSS JOIN search_by_keyword 
    ON RU.postal_code = Address.postal_code 
    WHERE RU.email = %s
    ORDER BY distance, item_id ASC
    """

    args = user_id, key_word, key_word, user_id,

    return execute(sql, args)


def search_by_postal_code(user_id, postal_code):
    sql = """
    WITH search_by_keyword AS (
    SELECT item_id, RU.email, game_type,title, item_condition, item_description, RU.postal_code, longitude, latitude
    FROM Item
        JOIN RegularUser RU ON Item.email = RU.email
    JOIN Address ON Address.postal_code = RU.postal_code
    WHERE RU.email <> %s and RU.postal_code = %s
    AND item_id NOT IN
    (SELECT item_id as itemz
    FROM SwapRequest
    JOIN SwapRequestDetail ON SwapRequestDetail.swap_id=SwapRequest.swap_id
    WHERE SwapRequest.status = 'pending' OR SwapRequest.status = 'accepted')
    )
    SELECT search_by_keyword.email,search_by_keyword.item_id,search_by_keyword.game_type,search_by_keyword.title,search_by_keyword.item_condition,search_by_keyword.item_description, ROUND(haversine(Address.latitude, Address.longitude, search_by_keyword.latitude, search_by_keyword.longitude), 2) AS `distance` 
    FROM RegularUser RU JOIN Address 
    CROSS JOIN search_by_keyword 
    ON RU.postal_code = Address.postal_code 
    WHERE RU.email = %s
    ORDER BY distance, item_id ASC
    """
    args = user_id, postal_code, user_id,

    return execute(sql, args)


def search_by_distance(user_id, distance):
    sql = """
    WITH distance_table AS(
    WITH search_by_keyword AS (
    SELECT item_id, RU.email, game_type,title, item_condition, item_description, RU.postal_code, longitude, latitude
    FROM Item
        JOIN RegularUser RU ON Item.email = RU.email
    JOIN Address ON Address.postal_code = RU.postal_code
    WHERE RU.email <> %s 
    AND item_id NOT IN
    (SELECT item_id as itemz
    FROM SwapRequest
    JOIN SwapRequestDetail ON SwapRequestDetail.swap_id=SwapRequest.swap_id
    WHERE SwapRequest.status = 'pending' OR SwapRequest.status = 'accepted')
    )
    SELECT search_by_keyword.email,search_by_keyword.item_id,search_by_keyword.game_type,search_by_keyword.title,search_by_keyword.item_condition,search_by_keyword.item_description, ROUND(haversine(Address.latitude, Address.longitude, search_by_keyword.latitude, search_by_keyword.longitude), 2) AS `distance` 
    FROM RegularUser RU JOIN Address 
    CROSS JOIN search_by_keyword 
    ON RU.postal_code = Address.postal_code 
    WHERE RU.email = %s
    ORDER BY distance, item_id ASC)
    SELECT * FROM distance_table WHERE distance < %s
    """

    args = user_id, user_id, distance,

    return execute(sql, args)


def postal_code_exist(postal_code):
    sql = """
    SELECT postal_code FROM Address  
    WHERE postal_code = %s
    """

    args = postal_code,

    return execute(sql, args)


def get_selected_details(user_id, item_id):
    sql = """
    WITH selected_id AS (
    SELECT first_name,last_name,city,state, item_id, RU.email, game_type,title, item_condition, item_description, RU.postal_code, longitude, latitude
    FROM Item
            JOIN RegularUser RU ON Item.email = RU.email
    JOIN Address ON Address.postal_code = RU.postal_code
    WHERE item_id = %s
    )
    SELECT selected_id.*, ROUND(haversine(Address.latitude, Address.longitude, selected_id.latitude, selected_id.longitude), 2) AS `distance` 
    FROM RegularUser RU JOIN Address 
    CROSS JOIN selected_id 
    ON RU.postal_code = Address.postal_code 
    WHERE RU.email = %s
    """
    args = item_id, user_id,
    return execute(sql, args)


def video_game(item_id):
    sql = """
    SELECT * FROM VideoGameItem
    WHERE item_id = %s
    """
    args = item_id,
    return execute(sql, args)


def jigsaw_puzzle(item_id):
    sql = """
    SELECT * FROM JigsawPuzzleItem
    WHERE item_id = %s
    """
    args = item_id,
    return execute(sql, args)


def computer_game(item_id):
    sql = """
    SELECT * FROM ComputerGameItem
    WHERE item_id = %s
    """
    args = item_id,
    return execute(sql, args)


def get_proposer_id(swap_id):
    sql = """
        SELECT party
        FROM SwapRequestDetail
        WHERE swap_id = %s
        AND is_proposer = 1
    """
    args = swap_id,
    user_id = execute(sql, args)[0]['party']
    return user_id


def accept_swap(swap_id):
    sql = """
        UPDATE SwapRequest
        SET status = "accepted", completion_date = CURDATE()
        WHERE swap_id = %s
    """
    args = swap_id,
    execute(sql, args)


def reject_swap(swap_id):
    sql = """
        UPDATE SwapRequest
        SET status = "rejected", completion_date = CURDATE()
        WHERE swap_id = %s
    """
    args = swap_id,
    execute(sql, args)

