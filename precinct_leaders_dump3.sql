--
-- PostgreSQL database dump
--

\restrict B11TYRJPPj7KVe6gFayrjBEsDOqUkJicZT8abIQmiph4YfecJXYRpwhy7f6KYjv

-- Dumped from database version 17.6 (Ubuntu 17.6-2.pgdg24.04+1)
-- Dumped by pg_dump version 17.6 (Ubuntu 17.6-2.pgdg24.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: precinct_leaders; Type: TABLE; Schema: public; Owner: bren
--

CREATE TABLE public.precinct_leaders (
    id integer NOT NULL,
    "position" character varying(50) NOT NULL,
    term character varying(10) NOT NULL,
    precinct_id character varying(10) NOT NULL,
    citizen_name character varying(100) NOT NULL,
    phone character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    email character varying(40),
    password character varying(30) NOT NULL,
    password_hash character varying(50) NOT NULL
);


ALTER TABLE public.precinct_leaders OWNER TO bren;

--
-- Name: TABLE precinct_leaders; Type: COMMENT; Schema: public; Owner: bren
--

COMMENT ON TABLE public.precinct_leaders IS 'Stores information about precinct leaders including chairs and their contact information';


--
-- Name: COLUMN precinct_leaders."position"; Type: COMMENT; Schema: public; Owner: bren
--

COMMENT ON COLUMN public.precinct_leaders."position" IS 'Leadership position (e.g., Chair, Vice Chair)';


--
-- Name: COLUMN precinct_leaders.term; Type: COMMENT; Schema: public; Owner: bren
--

COMMENT ON COLUMN public.precinct_leaders.term IS 'Term period in format YY-YY (e.g., 23-25)';


--
-- Name: COLUMN precinct_leaders.precinct_id; Type: COMMENT; Schema: public; Owner: bren
--

COMMENT ON COLUMN public.precinct_leaders.precinct_id IS 'Precinct identifier, stored as text to preserve leading zeros';


--
-- Name: COLUMN precinct_leaders.citizen_name; Type: COMMENT; Schema: public; Owner: bren
--

COMMENT ON COLUMN public.precinct_leaders.citizen_name IS 'Full name in Last, First Middle format';


--
-- Name: COLUMN precinct_leaders.phone; Type: COMMENT; Schema: public; Owner: bren
--

COMMENT ON COLUMN public.precinct_leaders.phone IS 'Contact phone number';


--
-- Name: precinct_leaders_id_seq; Type: SEQUENCE; Schema: public; Owner: bren
--

CREATE SEQUENCE public.precinct_leaders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.precinct_leaders_id_seq OWNER TO bren;

--
-- Name: precinct_leaders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bren
--

ALTER SEQUENCE public.precinct_leaders_id_seq OWNED BY public.precinct_leaders.id;


--
-- Name: precinct_leaders id; Type: DEFAULT; Schema: public; Owner: bren
--

ALTER TABLE ONLY public.precinct_leaders ALTER COLUMN id SET DEFAULT nextval('public.precinct_leaders_id_seq'::regclass);


--
-- Data for Name: precinct_leaders; Type: TABLE DATA; Schema: public; Owner: bren
--

COPY public.precinct_leaders (id, "position", term, precinct_id, citizen_name, phone, created_at, updated_at, email, password, password_hash) FROM stdin;
155	VC	25-27	401	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
156	Sec	25-27	401	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
160	Chair	25-27	405	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
161	VC	25-27	405	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
162	Sec	25-27	405	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
169	Chair	25-27	806	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
170	VC	25-27	806	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
171	Sec	25-27	806	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
172	Chair	25-27	808	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
173	VC	25-27	808	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
269	Chair	25-27	702	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
270	Chair	25-27	075	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
271	Chair	25-27	015	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
272	Chair	25-27	043	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
273	Chair	25-27	909	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
274	Chair	25-27	801	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
275	Chair	25-27	302	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
276	Chair	25-27	062	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
277	Chair	25-27	016	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
278	Chair	25-27	092	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
279	Chair	25-27	606	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
280	Chair	25-27	205	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
281	Chair	25-27	033	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
174	Sec	25-27	808	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
178	Chair	25-27	301	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
179	VC	25-27	301	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
180	Sec	25-27	301	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
181	Chair	25-27	304	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
182	VC	25-27	304	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
183	Sec	25-27	304	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
184	Chair	25-27	306	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
185	VC	25-27	306	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
186	Sec	25-27	306	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
193	Chair	25-27	707	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
194	VC	25-27	707	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
195	Sec	25-27	707	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
199	Chair	25-27	708	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
200	VC	25-27	708	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
201	Sec	25-27	708	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
208	Chair	25-27	206	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
209	VC	25-27	206	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
210	Sec	25-27	206	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
1	Chair	23-25	031	Crews, Beverly S	(336) 391-4808	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
2	Chair	23-25	051	Caroon, Suzanne N	(336) 682-0694	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
3	Chair	23-25	052	Nelligan, Janice S	(336) 817-6567	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
4	Chair	23-25	053	Cook, Alice J	(336) 403-8688	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
5	Chair	23-25	054	Heath, Jack C	(336) 904-3284	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
6	Chair	23-25	055	Arrigo, Linda M	(336) 289-5102	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
7	Chair	23-25	061	Jones, Robert E	(336) 408-6970	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
8	Chair	23-25	063	Burrell, Shari R	(336) 575-6989	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
9	Chair	23-25	065	Counts, Percilla S	(828) 964-3441	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
10	Chair	23-25	067	Click, Rudolph J	(336) 817-2617	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
11	Chair	23-25	071	Wilder, Mack H	(336) 608-8433	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
12	Chair	23-25	073	Chrysson, Jennifer W	(336) 775-7168	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
13	Chair	23-25	074	Phillips, Matilda D	(215) 740-1746	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
14	Chair	23-25	076	Wiles, Susan W	(336) 473-5692	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
15	Chair	23-25	077	Muck, Eric C	(336) 480-5360	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
16	Chair	23-25	081	Pender, Randon B	(336) 575-2006	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
17	Chair	23-25	083	Lindsay, Andrew W	(336) 407-2510	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
18	Chair	23-25	084	Funderburk, Rodney T	(336) 997-1640	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
19	Chair	23-25	101	McCaskill, Reginald D	(336) 416-6775	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
20	Chair	23-25	112	Motsinger, Elisabeth M	(336) 816-8666	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
282	Chair	25-27	017	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
283	Chair	25-27	012	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
284	Chair	25-27	091	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
285	Chair	25-27	032	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
286	Chair	25-27	034	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
287	Chair	25-27	042	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
288	Chair	25-27	013	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
289	Chair	25-27	085	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
290	Chair	25-27	066	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
291	Chair	25-27	404	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
214	Chair	25-27	208	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
215	VC	25-27	208	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
216	Sec	25-27	208	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
220	Chair	25-27	602	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
221	VC	25-27	602	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
222	Sec	25-27	602	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
229	Chair	25-27	605	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
230	VC	25-27	605	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
231	Sec	25-27	605	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
232	Chair	25-27	607	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
233	VC	25-27	607	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
234	Sec	25-27	607	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
241	Chair	25-27	503	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
242	VC	25-27	503	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
85	Chair	25-27	103	Fletcher, Tamatha Leann	(336) 924-2671	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
86	Chair	25-27	104	Slate, William Bradley	(336) 924-0515	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
87	Chair	25-27	111	Baggett, Robin Ayne	(336) 924-7527	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
88	Chair	25-27	112	Moody, Sharon Lynn	(336) 924-5939	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
89	Chair	25-27	113	Mitchell, James Michael	(336) 924-4499	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
90	Chair	25-27	114	Burns, James Robert	(336) 924-5967	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
91	Chair	25-27	121	Morton, Caroline Reeves	(336) 924-7339	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
92	Chair	25-27	122	Davis, Joyce Christine	(336) 924-2555	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
93	Chair	25-27	123	Wallace, Nancy Jane	(336) 924-7279	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
94	Chair	25-27	124	Hutchins, Michael Lane	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
95	Chair	25-27	131	Canter, Joseph Paul	(336) 924-5835	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
96	Chair	25-27	132	Wood, Janet Kaye	(336) 924-3287	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
97	Chair	25-27	133	Petree, Susan Leigh	(336) 924-8659	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
98	Chair	25-27	134	Knight, Danny Ray	(336) 924-5147	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
99	Chair	25-27	141	Davis, Pamela Sue	(336) 924-4919	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
263	Chair	25-27	14	open	not set	2025-10-20 09:04:56.804106	2025-10-20 09:04:56.804106	\N	not set	not set
264	Chair	25-27	014	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
266	Chair	25-27	068	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
267	Chair	25-27	064	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
268	Chair	25-27	705	open	not set	2025-10-20 09:06:20.064566	2025-10-20 09:06:20.064566	\N	not set	not set
136	Chair	25-27	904	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
137	VC	25-27	904	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
138	Sec	25-27	904	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
139	Chair	25-27	905	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
140	VC	25-27	905	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
141	Sec	25-27	905	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
154	Chair	25-27	401	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
100	Chair	25-27	142	Ward, Barbara Jean	(336) 924-7403	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
101	Chair	25-27	143	Gaddy, Brenda Kay	(336) 924-2703	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
102	Chair	25-27	144	Yokeley, Michelle Dawn	(336) 924-7747	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
103	Chair	25-27	151	Hege, Dawn Renee	(336) 924-3123	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
104	Chair	25-27	152	Poindexter, Crystal Dawn	(336) 924-5383	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
105	Chair	25-27	153	Hutchins, Rebecca Sue	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
106	Chair	25-27	154	Hutchins, Joseph Michael	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
107	Chair	25-27	161	Gaddy, James Franklin	(336) 924-2415	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
108	Chair	25-27	162	Hutchins, James Edward	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
109	Chair	25-27	163	Carter, Susan Lynne	(336) 924-5283	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
110	Chair	25-27	164	Hutchins, Rebecca Jane	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
111	Chair	25-27	171	Hutchins, James Michael	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
112	Chair	25-27	172	Carter, William Eugene	(336) 924-5283	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
113	Chair	25-27	173	Hutchins, Joseph Edward	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
114	Chair	25-27	174	Hutchins, William James	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
115	Chair	25-27	181	Hutchins, Rebecca Dawn	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
116	Chair	25-27	182	Carter, Susan Jane	(336) 924-5283	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
117	Chair	25-27	183	Hutchins, James William	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
118	Chair	25-27	184	Carter, William James	(336) 924-5283	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
119	Chair	25-27	191	Hutchins, Joseph William	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
120	Chair	25-27	192	Carter, Rebecca Sue	(336) 924-5283	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
121	Chair	25-27	193	Hutchins, William Joseph	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
122	Chair	25-27	194	Carter, James Eugene	(336) 924-5283	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
123	Chair	25-27	201	Hutchins, Rebecca William	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
124	Chair	25-27	202	Carter, Susan Eugene	(336) 924-5283	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
125	Chair	25-27	203	Hutchins, Joseph James	(336) 924-1847	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
22	Chair	23-25	131	Spencer, Benjamin E	(336) 703-8878	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
33	Chair	23-25	501	Wallace, Bernard	(336) 354-8652	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
34	Chair	23-25	502	Corley, Norma E	(336) 624-5980	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
35	Chair	23-25	504	Boyd, Jimmie L	(336) 972-7082	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
36	Chair	23-25	505	Bailey, Rosa B	(336) 624-3271	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
37	Chair	23-25	601	Benson, James K	(336) 414-9431	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
38	Chair	23-25	603	Barr, Matthew F	(336) 408-7961	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
39	Chair	23-25	604	Lechleider, Lucinda H	(336) 682-6369	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
40	Chair	23-25	701	Gaither, Lessie B	(336) 749-9798	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
41	Chair	23-25	703	Gledhill, James T	(336) 705-2228	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
42	Chair	23-25	704	Pounds, Kathleen B	(513) 302-0998	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
43	Chair	23-25	706	Besse, Daniel V	(336) 775-7877	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
44	Chair	23-25	709	Reisman, Gwendolyn A	(201) 406-1423	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
45	Chair	23-25	802	Whitman, Ariel U	(336) 317-5968	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
46	Chair	23-25	803	Cruikshank, Lila J	(609) 915-1674	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
47	Chair	23-25	804	Virgil, Steven M	(336) 529-9043	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
25	Chair	23-25	135	Debrecht, Deanna L	(203) 560-4962	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
26	Chair	23-25	202	Campbell, Eunice Y	(336) 918-4238	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
27	Chair	23-25	204	West, David L	(336) 575-6292	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
28	Chair	23-25	207	Lavery, Pearle R	(336) 926-8556	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
29	Chair	23-25	303	Boone, Michelle G	(336) 624-2113	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
30	Chair	23-25	305	Crumb, Kenneth T	(336) 293-3594	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
31	Chair	23-25	402	Washington, Demeca J	(336) 995-6248	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
32	Chair	23-25	403	Porter, Albert T	(336) 816-4277	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
48	Chair	23-25	805	Black, Tammy K	(336) 682-1434	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
49	Chair	23-25	807	Holley, Stacy K	(336) 202-9472	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
50	Chair	23-25	809	Sadler, Orin W	(336) 252-8812	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
51	Chair	23-25	901	Gray, Dennis E	(703) 336-2587	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
52	Chair	23-25	902	Freimuth, Alicia C	(804) 245-5065	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
53	Chair	23-25	903	Wigodsky, John D	(336) 655-7036	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
54	Chair	23-25	906	Keller, Anna S	(770) 324-7335	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
55	Chair	23-25	907	Norris, Randy E	(336) 414-8635	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
56	Chair	23-25	908	Gayzik, Albert	(732) 470-4210	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
83	Chair	25-27	101	Ford, Christopher Shane	(336) 924-5755	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
84	Chair	25-27	102	Johnson, Nancy Mae	(336) 924-4111	2025-10-07 19:03:55.11901	2025-10-07 19:03:55.11901	\N	not set	not set
243	Sec	25-27	503	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
21	Chair	23-25	124	Cates Allen, Mackenzie	(336) 775-7102	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
23	Chair	23-25	132	Larrabee, Kara H	(843) 810-1812	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
24	Chair	23-25	134	Newsome, Suzanne	(336) 608-8217	2025-10-06 15:11:23.984578	2025-10-06 15:11:23.984578	\N	not set	not set
247	Chair	25-27	506	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
248	VC	25-27	506	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
249	Sec	25-27	506	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
253	Chair	25-27	508	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
254	VC	25-27	508	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
255	Sec	25-27	508	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
256	Chair	25-27	509	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
257	VC	25-27	509	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
258	Sec	25-27	509	open	not set	2025-10-07 22:03:21.01932	2025-10-07 22:03:21.01932	\N	not set	not set
262	Chair	25-27	021	open	not set	2025-10-20 09:01:42.16492	2025-10-20 09:01:42.16492	\N	not set	not set
\.


--
-- Name: precinct_leaders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: bren
--

SELECT pg_catalog.setval('public.precinct_leaders_id_seq', 338, true);


--
-- Name: precinct_leaders precinct_leaders_pkey; Type: CONSTRAINT; Schema: public; Owner: bren
--

ALTER TABLE ONLY public.precinct_leaders
    ADD CONSTRAINT precinct_leaders_pkey PRIMARY KEY (id);


--
-- Name: precinct_leaders uk_precinct_leaders_position_term_precinct_name; Type: CONSTRAINT; Schema: public; Owner: bren
--

ALTER TABLE ONLY public.precinct_leaders
    ADD CONSTRAINT uk_precinct_leaders_position_term_precinct_name UNIQUE ("position", term, precinct_id, citizen_name);


--
-- Name: CONSTRAINT uk_precinct_leaders_position_term_precinct_name ON precinct_leaders; Type: COMMENT; Schema: public; Owner: bren
--

COMMENT ON CONSTRAINT uk_precinct_leaders_position_term_precinct_name ON public.precinct_leaders IS 'Ensures unique combination of position, term, precinct_id, and citizen_name to prevent duplicate leader entries while allowing same person to serve different roles or different precincts';


--
-- Name: idx_precinct_leaders_position; Type: INDEX; Schema: public; Owner: bren
--

CREATE INDEX idx_precinct_leaders_position ON public.precinct_leaders USING btree ("position");


--
-- Name: idx_precinct_leaders_precinct; Type: INDEX; Schema: public; Owner: bren
--

CREATE INDEX idx_precinct_leaders_precinct ON public.precinct_leaders USING btree (precinct_id);


--
-- Name: idx_precinct_leaders_term; Type: INDEX; Schema: public; Owner: bren
--

CREATE INDEX idx_precinct_leaders_term ON public.precinct_leaders USING btree (term);


--
-- PostgreSQL database dump complete
--

\unrestrict B11TYRJPPj7KVe6gFayrjBEsDOqUkJicZT8abIQmiph4YfecJXYRpwhy7f6KYjv

