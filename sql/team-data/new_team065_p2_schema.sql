# Do not drop our remote database, only drop locally!
-- DROP DATABASE IF EXISTS `dev`; 
SET default_storage_engine=InnoDB;
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `dev`
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;
USE `dev`;

-- TABLES
CREATE TABLE Address (
    postal_code VARCHAR(5) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(2) NOT NULL,
    latitude DECIMAL(8 , 6 ) NOT NULL,
    longitude DECIMAL(9 , 6 ) NOT NULL,
    PRIMARY KEY (postal_code)
);

CREATE TABLE RegularUser (
    email VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    postal_code VARCHAR(5) NOT NULL,
    PRIMARY KEY (email),
    FOREIGN KEY (postal_code)
        REFERENCES Address (postal_code)
);
  
CREATE TABLE PhoneNumber (
    email VARCHAR(50) NOT NULL,
    number VARCHAR(20) NOT NULL,
    type VARCHAR(50) NOT NULL,
    share BIT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (number),
    FOREIGN KEY (email)
        REFERENCES RegularUser (email),
    CONSTRAINT `chk_phone_type` CHECK (type IN ('home' , 'work', 'mobile'))
);
 
CREATE TABLE Item (
    item_id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(50) NOT NULL,
    item_description VARCHAR(280),
    title VARCHAR(50) NOT NULL,
    item_condition VARCHAR(50) NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    PRIMARY KEY (item_id),
    FOREIGN KEY (email)
        REFERENCES RegularUser (email),
    CONSTRAINT `chk_item_condition` CHECK (item_condition IN ('Mint' , 'Like New',
        'Lightly Used',
        'Moderately Used',
        'Heavily Used',
        'Damaged/Missing parts')),
    CONSTRAINT `chk_game_type` CHECK (game_type IN ('Board game' , 'Card game',
        'Video game',
        'Computer game',
        'Jigsaw puzzle'))
);
 
CREATE TABLE VideoGamePlatform (
    video_game_platform VARCHAR(50) NOT NULL,
    PRIMARY KEY (video_game_platform)
);
 
CREATE TABLE VideoGameItem (
    item_id INT NOT NULL,
    video_game_platform VARCHAR(50) NOT NULL,
    media VARCHAR(50) NOT NULL,
    PRIMARY KEY (item_id),
    FOREIGN KEY (item_id)
        REFERENCES Item (item_id),
    FOREIGN KEY (video_game_platform)
        REFERENCES VideoGamePlatform (video_game_platform),
    CONSTRAINT `chk_media` CHECK (media IN ('optical disc' , 'game card', 'cartridge'))
);

CREATE TABLE JigsawPuzzleItem (
    item_id INT NOT NULL,
    piece_count INT NOT NULL,
    PRIMARY KEY (item_id),
    FOREIGN KEY (item_id)
        REFERENCES Item (item_id)
);

CREATE TABLE ComputerGameItem (
    item_id INT NOT NULL,
    computer_platform VARCHAR(50) NOT NULL,
    PRIMARY KEY (item_id),
    FOREIGN KEY (item_id)
        REFERENCES Item (item_id),
    CONSTRAINT `chk_computer_platform` CHECK (computer_platform IN ('Linux' , 'macOS', 'Windows'))
);

CREATE TABLE SwapRequest (
	swap_id INT AUTO_INCREMENT,
    proposal_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    completion_date DATE,
    distance DECIMAL(10 , 1 ) NOT NULL,
    PRIMARY KEY (swap_id)
);

CREATE TABLE SwapRequestDetail (
	swap_id INT,
    item_id INT,
    party VARCHAR(50),
    is_proposer BOOL,
    rating TINYINT UNSIGNED,
    PRIMARY KEY (swap_id, item_id),
    FOREIGN KEY (swap_id) REFERENCES SwapRequest (swap_id),
    FOREIGN KEY (item_id) REFERENCES Item (item_id),
    UNIQUE KEY (swap_id, party),
    CONSTRAINT `chk_rating` CHECK (rating <= 5)
);

ALTER TABLE SwapRequest 
ADD CONSTRAINT `chk_status` CHECK (status IN ('accepted', 'rejected', 'pending'))
;
ALTER TABLE SwapRequestDetail
ADD CONSTRAINT UNIQUE (swap_id, is_proposer)

