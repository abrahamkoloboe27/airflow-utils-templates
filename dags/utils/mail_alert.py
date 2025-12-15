
def success_callback(context: Dict[str, Any], mails_list, corporate, message) -> None:
    """
    Callback function called when the DAG execution is successful.
    Sends a success notification email to specified recipients.

    Args:
        context: Dict[str, Any]
            Airflow context dictionary containing execution information:
            - dag: The DAG object
            - ts: Execution timestamp

    Returns:
        None
    """
    from datetime import datetime 
    from airflow.utils.email import send_email_smtp
    
    send_email_smtp(
        to=mails_list,
        subject=f' {corporate} DAG xxxxxxxxx - Exécution Réussie',
        html_content=f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'>
            <div style='background-color: #4CAF50; padding: 30px 20px; border-radius: 5px 5px 0 0; text-align: center;'>
                <h2 style='color: white; margin: 0; font-size: 24px; line-height: 1.4;'>
                    ✅ Exécution Réussie | Successful Execution
                </h2>
            </div>
            <div style='background-color: #ffffff; padding: 30px 25px; border-radius: 0 0 5px 5px; border: 1px solid #e9ecef; border-top: none;'>
                <p style='color: #34495e; line-height: 1.6; margin: 0 0 20px 0;'>
                    <strong>DAG:</strong> {context['dag'].dag_id}<br>
                    <strong>Date d'exécution | Execution Date:</strong> {context['ts']}<br>
                </p>
                <p style='color: #34495e; line-height: 1.6; margin: 0;'>
                    {message}
                </p>
            </div>
            <div style='text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef;'>
                <p style='color: #7f8c8d; font-size: 12px; line-height: 1.4; margin: 0;'>
                    Ceci est un message automatique. | This is an automated message.<br>
                    © {corporate} - {datetime.now().year}
                </p>
            </div>
        </div>
        """
    )

def failure_callback(context: Dict[str, Any], mails_list, corporate) -> None:
    """
    Callback function called when the DAG execution fails.
    Sends a failure notification email to specified recipients with error details.

    Args:
        context: Dict[str, Any]
            Airflow context dictionary containing execution information:
            - dag: The DAG object
            - ts: Execution timestamp
            - exception: The exception that caused the failure

    Returns:
        None
    """
    from datetime import datetime 
    from airflow.utils.email import send_email_smtp
    send_email_smtp(
        to= mails_list ,
        subject=f'{corporate} DAG xxxxxxx - Échec Critique ⚠️',
        html_content=f"""
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'>
            <div style='background-color: #FF5252; padding: 30px 20px; border-radius: 5px 5px 0 0; text-align: center;'>
                <h2 style='color: white; margin: 0; font-size: 24px; line-height: 1.4;'>
                    ⚠️ Échec Détecté | Failure Detected
                </h2>
            </div>
            <div style='background-color: #ffffff; padding: 30px 25px; border-radius: 0 0 5px 5px; border: 1px solid #e9ecef; border-top: none;'>
                <p style='color: #34495e; line-height: 1.6; margin: 0 0 20px 0;'>
                    <strong>DAG:</strong> {context['dag'].dag_id}<br>
                    <strong>Date d'exécution | Execution Date:</strong> {context['ts']}<br>
                    <strong>Erreur | Error:</strong><br>
                    <code style='background: #f8f9fa; padding: 10px; display: block; margin-top: 10px; border-radius: 4px;'>
                        {context['exception']}
                    </code>
                </p>
                <p style='color: #34495e; line-height: 1.6; margin: 0;'>
                    Une intervention immédiate est requise pour résoudre ce problème.<br>
                    Immediate attention is required to resolve this issue.
                </p>
            </div>
            <div style='text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef;'>
                <p style='color: #7f8c8d; font-size: 12px; line-height: 1.4; margin: 0;'>
                    Ceci est un message automatique. | This is an automated message.<br>
                    © {corporate} - {datetime.now().year}
                </p>
            </div>
        </div>
        """
    )
