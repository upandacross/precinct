drop table if exists temp_oppo;                                                                                                    
create temporary table temp_oppo as
select precinct, election_date, contest_name, max(total_votes) as oppo_votes
from candidate_vote_results where choice_party != 'DEM' group by precinct, election_date, contest_name;

drop table if exists temp_dem; 
create temporary table temp_dem as
select precinct, election_date, contest_name, choice_party, total_votes as dem_votes
from candidate_vote_results where choice_party = 'DEM';

\out lost_races.txt
select LPAD(d.precinct::text, 3, '0') as padded_precinct, count(distinct(d.election_date, d.contest_name)) as losses from temp_dem as d
left join temp_oppo as o on
d.precinct = o.precinct and
d.election_date = o.election_date and
d.contest_name = o.contest_name
where  (dem_votes - oppo_votes) < 0 group by padded_precinct;
\out

drop table if exists temp_oppo;
drop table if exists temp_dem;

select 'results in lost_races.txt';
