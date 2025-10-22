CREATE TABLE public.maps (
    id integer NOT NULL,
    state character varying(100) NOT NULL,
    county character varying(100) NOT NULL,
    precinct character varying(100) NOT NULL,
    map text,
    created_at timestamp without time zone
);


ALTER TABLE public.maps OWNER TO postgres;
