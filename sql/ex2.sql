
-- Q1
CREATE OR REPLACE VIEW V_Client AS
SELECT c.CodeC AS code,
       c.Prenom AS prenom,
       c.Nom AS nom,
       c.age AS age,
       SUM(l.km) AS distance
FROM CLIENT c
LEFT JOIN LOCATION l ON c.CodeC = l.CodeC
GROUP BY c.CodeC, c.Prenom, c.Nom, c.age;

-- Q2
UPDATE V_Client
SET prenom = 'Pierre' WHERE code = 'C672';
-- à chaque action on a une erreur "data manipulation operation not legal on this view", donc on doit mettre en place un trigger pour 
-- autoriser les updates sur la vue

-- trigger pour update une vue 
CREATE OR REPLACE TRIGGER trg_update_v_client
INSTEAD OF UPDATE ON V_Client
FOR EACH ROW
BEGIN
    UPDATE CLIENT
    SET Nom = :NEW.nom,
        Prenom = :NEW.prenom,
        age = :NEW.age
    WHERE CodeC = :OLD.code;
END;


SELECT * FROM V_Client;


-- Q3
CREATE OR REPLACE VIEW V_Client55 AS
SELECT CodeC AS code,
       Prenom AS prenom,
       Nom AS nom,
       age
FROM CLIENT
WHERE age > 55;

SELECT * FROM V_Client55;

-- Q4
INSERT INTO V_Client55 (code, prenom, nom, age)
VALUES ('C999', 'Luc', 'Martin', 50);
-- la ligne a été ajoutée dans la table client mais n'est pas affiché dans la vue V_Client55
-- on le visualise donc grace à la vu V_Client
SELECT * FROM V_Client WHERE code='C999';


