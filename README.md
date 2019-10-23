BesanconWorker
=============
Besoncon model models distribution of the stars in the Milky Way galaxy. 
``BesanconWorker`` is a python class which provides a set of methods to run several 
jobs on Besoncon web service. It BesanconWorker object can login, create job,
fill job form, submit job, download result, and delete job. The user need to have
an account on https://model.obs-besancon.fr/ws/ (username and password).

As an example a script using main method is provided in 'run_query.py' file.
The script can be run in terminal by following argument:

-c : Chrome Driver address
-r : a fiolder address or saving the results
-p : a CSV file address including 'ra' and 'dec' columns for locations in the sky.
-a : area in degree^2, It should be between 0 and 42000

After running the script the user is prompted for entering the password.


