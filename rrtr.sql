insert into sv_provincia values(2,'La Habana') 
insert into sv_municipio values(2,'Playa',2)
insert into sv_municipio values(3,'Batabano',3)


insert into sv_municipio values(1,'Candelaria',1)

insert into sv_municipio values(4,'Jaruco',4)

CREATE TABLE sv_provincia (
	id serial PRIMARY KEY,
	nombre TEXT UNIQUE NOT NULL
);


CREATE TABLE sv_municipio (
  id serial PRIMARY KEY,
  nombre TEXT NOT NULL,
  provincia_id INT NOT NULL, 
  
  FOREIGN KEY (provincia_id)
      REFERENCES sv_provincia (id) 
);

INSERT INTO sv_provincia (id, nombre) VALUES (1, 'Pinar del Río');
INSERT INTO sv_provincia (id, nombre) VALUES (3, 'Artemisa');

INSERT INTO sv_provincia (id, nombre) VALUES (4, 'Mayabeque');
INSERT INTO sv_provincia (id, nombre) VALUES (5, 'Matanzas');
INSERT INTO sv_provincia (id, nombre) VALUES (6, 'Cienfuegos');
INSERT INTO sv_provincia (id, nombre) VALUES (7, 'Villa Clara');
INSERT INTO sv_provincia (id, nombre) VALUES (8, 'Sancti Spíritus');

INSERT INTO sv_provincia (id, nombre) VALUES (9, 'Ciego de Avila');
INSERT INTO sv_provincia (id, nombre) VALUES (10, 'Camagüey');
INSERT INTO sv_provincia (id, nombre) VALUES (11, 'Las Tunas');
INSERT INTO sv_provincia (id, nombre) VALUES (12, 'Granma');
INSERT INTO sv_provincia (id, nombre) VALUES (13, 'Holguín');
INSERT INTO sv_provincia (id, nombre) VALUES (14, 'Santiago de Cuba');
INSERT INTO sv_provincia (id, nombre) VALUES (15, 'Guantánamo');

select * from sv_muestreo

