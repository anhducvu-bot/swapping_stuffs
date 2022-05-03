DROP TRIGGER IF EXISTS checkSwapRequestItem;
DELIMITER $$
CREATE TRIGGER checkSwapRequestItem
BEFORE INSERT ON SwapRequestDetail
FOR EACH ROW
BEGIN
# To insert, an item must either have been rejected or was not previously traded
  IF EXISTS (SELECT * FROM SwapRequestDetail SD JOIN SwapRequest SR 
		ON SD.swap_id = SR.swap_id
		WHERE NEW.item_id = SD.item_id AND SR.status IN ('accepted', 'pending'))
  THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Item was already successfully traded or is pending';
# Make sure the party is indeed this item's owner
  ELSEIF NEW.party NOT IN (SELECT email FROM Item IT 
		WHERE IT.item_id = NEW.item_id)
  THEN
  SIGNAL SQLSTATE '02000' SET MESSAGE_TEXT = 'Item does not belong to this Party';
  END IF;

END$$
DELIMITER ;

