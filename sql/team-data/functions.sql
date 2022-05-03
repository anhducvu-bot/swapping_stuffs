DELIMITER $$
DROP FUNCTION IF EXISTS haversine$$
 
CREATE FUNCTION haversine(lat1 FLOAT, long1 FLOAT, lat2 FLOAT, long2 FLOAT) RETURNS FLOAT
    NO SQL DETERMINISTIC
    COMMENT 'Returns the distance in degrees on the Earth between two known points'
BEGIN
DECLARE distance_from_user FLOAT;
DECLARE delta_lat FLOAT;
DECLARE delta_long FLOAT;
DECLARE a FLOAT;
DECLARE c FLOAT;

SET delta_lat = RADIANS(lat2 - lat1);
SET delta_long = RADIANS(long2 - long1);

SET a = POWER(SIN(delta_lat/2), 2) + COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * POWER(SIN(delta_long/2), 2);
SET c = 2 * ATAN2(SQRT(a), SQRT(1 - a));
SET distance_from_user = 6371 * c;
# km -> miles
RETURN distance_from_user * 0.621371; 
END$$
 
DELIMITER ;

SELECT haversine(38.8976, -77.0366, 39.9496, -75.1503)

#====================== Display rating 
DELIMITER $$
DROP FUNCTION IF EXISTS getRating$$

CREATE FUNCTION getRating(email varchar(50)) RETURNS varchar(50)
    READS SQL DATA DETERMINISTIC
    COMMENT 'Returns rating by ID'
BEGIN
DECLARE ratingChar varchar(50);

SET ratingChar = (SELECT 
    IFNULL(ROUND(AVG(rating), 2), 'None')
FROM
    SwapRequestDetail
WHERE
    party = email
);

RETURN ratingChar;
END$$
 
DELIMITER ;
SELECT getRating('abernhard@gmail.com')
