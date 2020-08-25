from lti import OutcomeRequest
from nbgrader.api import Gradebook, MissingEntry
from nbgrader.plugins import ExportPlugin, BasePlugin
import os.path

class MoodleExporter(ExportPlugin):

    def export(self, gradebook):
        # Create the connection to the database
        with Gradebook('sqlite:///gradebook.db') as gb:

            # Loop over each assignment in the database
            for assignment in gb.assignments:
                print("Exporting...")
                print("     Course-ID: " + assignment.course_id)
                print("     Assignment-Name: " + assignment.name)

                # Loop over each student in the database
                for student in gb.students:

                    # Check if file with lis-Parameters exists
                    path = (
                        '/opt/tljh/exchange/' + assignment.course_id + ''
                        '/inbound/log/' + assignment.name + ''
                        '/' + student.id + '.txt'
                    )

                    if os.path.isfile(path):
                        print("         Student-ID: " + student.id)

                        # Get stored parameters from the file
                        parameters = {}
                        with open(path, 'r') as log:
                            lines = log.read().splitlines()
                            parameters = {
                                'lis_outcome_service_url': lines[0],
                                'lis_result_sourcedid': lines[1]
                            }

                        # Try to find the submission in the database. If it doesn't exist, the
                        # `MissingEntry` exception will be raised, which means the student
                        # didn't submit anything, so we assign them a score of zero.
                        try:
                            submission = gb.find_submission(assignment.name, student.id)
                        except MissingEntry:
                            parameters['score'] = 0.0
                        else:
                            # Four digits shown in Moodle
                            resultscore = round(submission.score/assignment.max_score, 4)
                            if resultscore > 1:
                                resultscore = 1
                            parameters['score'] = resultscore

                        self.post_grades(parameters)

                    else:
                        print("         No LTI-Parameters found for: " + student.id)

    def post_grades(self, parameters):
        
        # Secret of the external Tool
        consumer_key = 'aef4193cf141d02a2adde6a9d5afaff028d9bf23139a4d1def1ee224f7682ca0'
        consumer_secret = 'f0b884c83c858fd8078bd187c0c54c281a32df2653401b0c415dec63580dc847'

        # Create POST-Request
        outcome_request = OutcomeRequest({
            'consumer_key': consumer_key,
            'consumer_secret': consumer_secret,
            'lis_outcome_service_url': parameters['lis_outcome_service_url'],
            'lis_result_sourcedid': parameters['lis_result_sourcedid']
        })

        # Replace result in Moodle
        outcome_response = outcome_request.post_replace_result(parameters['score'])