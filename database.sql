--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: set_thread_id(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION set_thread_id() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
NEW.thread_id := new.id; return new;
end;
$$;


ALTER FUNCTION public.set_thread_id() OWNER TO postgres;

--
-- Name: avatars_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE avatars_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.avatars_id_seq OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: avatars; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE avatars (
    id bigint DEFAULT nextval('avatars_id_seq'::regclass),
    user_id bigint
);


ALTER TABLE public.avatars OWNER TO postgres;

--
-- Name: files_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE files_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.files_id_seq OWNER TO postgres;

--
-- Name: files; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE files (
    id bigint DEFAULT nextval('files_id_seq'::regclass),
    set_id bigint,
    url text,
    name text
);


ALTER TABLE public.files OWNER TO postgres;

--
-- Name: posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE posts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.posts_id_seq OWNER TO postgres;

--
-- Name: posts; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE posts (
    id bigint DEFAULT nextval('posts_id_seq'::regclass),
    thread_id bigint,
    user_id bigint,
    avatar_id bigint,
    style_id bigint,
    content text,
    dt timestamp without time zone
);


ALTER TABLE public.posts OWNER TO postgres;

--
-- Name: ops; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE ops (
    forum_id bigint,
    page_id bigint
)
INHERITS (posts);


ALTER TABLE public.ops OWNER TO postgres;

--
-- Name: pages; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE pages (
    id bigint DEFAULT nextval('avatars_id_seq'::regclass),
    user_id bigint,
    published boolean DEFAULT false
);


ALTER TABLE public.pages OWNER TO postgres;

--
-- Name: pages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE pages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pages_id_seq OWNER TO postgres;

--
-- Name: tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tokens_id_seq OWNER TO postgres;

--
-- Name: tokens; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tokens (
    id bigint DEFAULT nextval('tokens_id_seq'::regclass),
    user_id bigint,
    token text
);


ALTER TABLE public.tokens OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE users (
    id bigint DEFAULT nextval('users_id_seq'::regclass),
    username text,
    hash text,
    salt text,
    avatar bigint,
    page bigint
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY ops ALTER COLUMN id SET DEFAULT nextval('posts_id_seq'::regclass);


--
-- Name: ops_content_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY ops
    ADD CONSTRAINT ops_content_key UNIQUE (content);


--
-- Name: set_thread_id_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER set_thread_id_trigger BEFORE INSERT ON ops FOR EACH ROW EXECUTE PROCEDURE set_thread_id();


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

