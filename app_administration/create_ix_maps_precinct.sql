-- Name: ix_maps_precinct; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_maps_precinct ON public.maps USING btree (precinct);

