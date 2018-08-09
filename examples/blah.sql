create table BLAH (
	clm_integer integer not null,
        clm_tinyint tinyint default 0,
        clm_smallint smallint default 0,
        clm_bigint bigint default 0,
        clm_string varchar(32) default null,
        clm_decimal decimal default null,
        clm_float float default null,
        clm_timestamp timestamp default null,
        clm_point geography_point default null,
        clm_geography geography default null,
        PRIMARY KEY(clm_integer)
);
