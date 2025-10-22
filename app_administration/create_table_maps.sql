CREATE TABLE public.maps (
    id integer NOT NULL,
    state character varying(100) NOT NULL,
    county character varying(100) NOT NULL,
    precinct character varying(100) NOT NULL,
    map text,
    created_at timestamp without time zone
);


ALTER TABLE public.maps OWNER TO postgres;

--
-- Name: maps_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.maps_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.maps_id_seq OWNER TO postgres;

--
-- Name: maps_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.maps_id_seq OWNED BY public.maps.id;


--
-- Name: precinct_leaders; Type: TABLE; Schema: public; Owner: bren
--
