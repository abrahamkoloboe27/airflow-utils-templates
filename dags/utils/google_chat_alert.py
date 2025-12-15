"""
Module containing functions for sending Google Chat alerts for DAG executions.
"""

def send_success_alert(context):
    """
    Send a Google Chat alert for a successful DAG execution.
    
    Args:
        **context: The Airflow task context
    """
    GCHAT_CONNECTION = "google_chat_alert"
    import logging
    import requests
    from airflow.hooks.base_hook import BaseHook

    try:
        # Extract DAG information from context
        dag_id = context["dag"].dag_id
        task_id = context["task_instance"].task_id
        execution_date = context["execution_date"].strftime("%Y-%m-%d %H:%M:%S")
        start_date = context["task_instance"].start_date
        end_date = context["task_instance"].end_date
        try_number = context["task_instance"].try_number
        max_tries = context["task"].retries + 1  # +1 car la première tentative n'est pas un retry
        
        # Gérer les problèmes de timezone entre les datetimes
        if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
            # Si start_date a un fuseau horaire, s'assurer que end_date a le même
            if end_date and hasattr(end_date, 'tzinfo') and not end_date.tzinfo:
                end_date = end_date.replace(tzinfo=start_date.tzinfo)
        else:
            # Sinon, s'assurer que les deux sont sans fuseau horaire
            if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
            if end_date and hasattr(end_date, 'tzinfo') and end_date.tzinfo:
                end_date = end_date.replace(tzinfo=None)
                
        # Calculate execution time
        if start_date and end_date:
            execution_time = (end_date - start_date).total_seconds()
            hours, remainder = divmod(execution_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            execution_time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        else:
            execution_time_str = "Non disponible"
        
        # Obtenir la description du DAG
        dag_description = context["dag"].description if hasattr(context["dag"], "description") else "Aucune description disponible"
        
        # Prepare widgets for the card
        widgets = [
            {"textParagraph": {"text": f"<b>📅 Date d'exécution:</b> {execution_date}"}},
            {"textParagraph": {"text": f"<b>✅ Statut:</b> Succès"}},
            {"textParagraph": {"text": f"<b>🔍 Tâche:</b> {task_id}"}},
            {"textParagraph": {"text": f"<b>📝 Description:</b> {dag_description}"}},
            {"textParagraph": {"text": f"<b>🔢 Tentative:</b> {try_number} sur {max_tries}"}},
            {"textParagraph": {"text": f"<b>⏱️ Temps d'exécution:</b> {execution_time_str}"}},
            {"textParagraph": {"text": f"<b>🕒 Heure de départ:</b> {start_date.strftime('%H:%M:%S') if start_date else 'Non disponible'}"}},
            {"textParagraph": {"text": f"<b>🕕 Heure de fin:</b> {end_date.strftime('%H:%M:%S') if end_date else 'Non disponible'}"}}
        ]
        
        # Get Google Chat webhook URL from Airflow connection
        conn = BaseHook.get_connection(GCHAT_CONNECTION)
        webhook_url = conn.host
        if not webhook_url.startswith('http'):
            webhook_url = f"https://{webhook_url}"
            
        # Create a unique thread ID for this DAG run
        thread_id = f"{dag_id}_{context['execution_date'].strftime('%Y%m%d')}"
        
        # Prepare the card body
        body = {
            'cardsV2': [{
                'cardId': f"{dag_id}_success_alert",
                'card': {
                    'header': {
                        'title': f"DAG: {dag_id} {context['execution_date'].strftime('%Y-%m-%d')}",
                        'subtitle': "Exécution réussie",
                        'imageUrl': "https://img.icons8.com/color/48/checkmark--v1.png"
                    },
                    'sections': [
                        {
                            'widgets': widgets
                        }
                    ]
                }
            }]
        }
        
        # Add thread parameters to the URL
        if '?' not in webhook_url:
            thread_ref = f"?threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
        else:
            thread_ref = f"&threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
            
        full_url = f"{webhook_url}{thread_ref}"
        
        # Send the request
        response = requests.post(full_url, json=body)
        response.raise_for_status()
        logging.info(f"Successfully sent Google Chat success alert for DAG {dag_id}")
        
    except Exception as e:
        logging.error(f"Failed to send Google Chat success alert: {str(e)}")
        if 'response' in locals():
            logging.error(f"Response content: {getattr(response, 'text', 'No response')}")


def send_retry_alert(context):
    """
    Send a Google Chat alert when a task is being retried.
    
    Args:
        context: The Airflow task context
    """
    import logging
    import requests
    from datetime import datetime
    from airflow.hooks.base_hook import BaseHook

    GCHAT_CONNECTION = "google_chat_alert"
    
    try:
        # Extract exception from context
        exception = context.get('exception')
        
        # Extract DAG information from context
        dag_id = context["dag"].dag_id
        task_id = context["task_instance"].task_id
        execution_date = context["execution_date"].strftime("%Y-%m-%d %H:%M:%S")
        start_date = context["task_instance"].start_date
        
        # Gérer les problèmes de timezone entre les datetimes
        if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
            # Si start_date a un fuseau horaire, utiliser le même pour end_date
            end_date = datetime.now(start_date.tzinfo)
        else:
            # Sinon, utiliser un datetime sans fuseau horaire
            end_date = datetime.now()
            if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
        try_number = context["task_instance"].try_number
        max_tries = context["task"].retries + 1  # +1 because the first attempt is not a retry
        next_retry_datetime = context.get("next_retry_datetime")
        
        # Calculate execution time so far
        if start_date:
            execution_time = (end_date - start_date).total_seconds()
            hours, remainder = divmod(execution_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            execution_time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        else:
            execution_time_str = "Non disponible"
        
        # Get exception details
        exception_msg = str(exception) if exception else "Aucune erreur disponible"
        if len(exception_msg) > 500:
            exception_msg = exception_msg[:497] + "..."
        
        # Obtenir la description du DAG
        dag_description = context["dag"].description if hasattr(context["dag"], "description") else "Aucune description disponible"
        
        # Prepare widgets for the card
        widgets = [
            {"textParagraph": {"text": f"<b>📅 Date d'exécution:</b> {execution_date}"}},
            {"textParagraph": {"text": f"<b>🔄 Statut:</b> Retentative en cours"}},
            {"textParagraph": {"text": f"<b>🔍 Tâche en retentative:</b> {task_id}"}},
            {"textParagraph": {"text": f"<b>📝 Description:</b> {dag_description}"}},
            {"textParagraph": {"text": f"<b>🔢 Tentative:</b> {try_number} sur {max_tries}"}},
            {"textParagraph": {"text": f"<b>⏱️ Temps d'exécution jusqu'à présent:</b> {execution_time_str}"}},
            {"textParagraph": {"text": f"<b>🕒 Heure de départ:</b> {start_date.strftime('%H:%M:%S') if start_date else 'Non disponible'}"}},
            {"textParagraph": {"text": f"<b>🕕 Heure de l'échec:</b> {end_date.strftime('%H:%M:%S')}"}},
        ]
        
        # Add next retry time if available
        if next_retry_datetime:
            widgets.append({"textParagraph": {"text": f"<b>⏰ Prochaine tentative à:</b> {next_retry_datetime.strftime('%H:%M:%S')}"}}) 
        
        # Add error message
        widgets.append({"textParagraph": {"text": f"<b>⚠️ Erreur:</b> {exception_msg}"}})
        
        # Get Google Chat webhook URL from Airflow connection
        conn = BaseHook.get_connection(GCHAT_CONNECTION)
        webhook_url = conn.host
        if not webhook_url.startswith('http'):
            webhook_url = f"https://{webhook_url}"
            
        # Create a unique thread ID for this DAG run
        thread_id = f"{dag_id}_{context['execution_date'].strftime('%Y%m%d')}"
        
        # Prepare the card body
        body = {
            'cardsV2': [{
                'cardId': f"{dag_id}_retry_alert",
                'card': {
                    'header': {
                        'title': f"DAG: {dag_id} {context['execution_date'].strftime('%Y-%m-%d')}",
                        'subtitle': f"Retentative {try_number}/{max_tries}",
                        'imageUrl': "https://img.icons8.com/color/48/synchronize--v1.png"
                    },
                    'sections': [
                        {
                            'widgets': widgets
                        }
                    ]
                }
            }]
        }
        
        # Add thread parameters to the URL
        if '?' not in webhook_url:
            thread_ref = f"?threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
        else:
            thread_ref = f"&threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
            
        full_url = f"{webhook_url}{thread_ref}"
        
        # Send the request
        response = requests.post(full_url, json=body)
        response.raise_for_status()
        logging.info(f"Successfully sent Google Chat retry alert for DAG {dag_id}")
        
    except Exception as e:
        logging.error(f"Failed to send Google Chat retry alert: {str(e)}")
        if 'response' in locals():
            logging.error(f"Response content: {getattr(response, 'text', 'No response')}")


def send_failure_alert(context):
    """
    Send a Google Chat alert for a failed DAG execution.
    
    Args:
        context: The Airflow task context
    """
    import logging
    import requests
    from datetime import datetime
    from airflow.hooks.base_hook import BaseHook

    GCHAT_CONNECTION = "google_chat_alert"
    
    try:
        # Extract exception from context
        exception = context.get('exception')
        
        # Extract DAG information from context
        dag_id = context["dag"].dag_id
        task_id = context["task_instance"].task_id
        execution_date = context["execution_date"].strftime("%Y-%m-%d %H:%M:%S")
        start_date = context["task_instance"].start_date
        try_number = context["task_instance"].try_number
        max_tries = context["task"].retries + 1  
        
        # Gérer les problèmes de timezone entre les datetimes
        if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
            # Si start_date a un fuseau horaire, utiliser le même pour end_date
            end_date = datetime.now(start_date.tzinfo)
        else:
            # Sinon, utiliser un datetime sans fuseau horaire
            end_date = datetime.now()
            if start_date and hasattr(start_date, 'tzinfo') and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
        
        # Calculate execution time
        if start_date:
            execution_time = (end_date - start_date).total_seconds()
            hours, remainder = divmod(execution_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            execution_time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        else:
            execution_time_str = "Non disponible"
        
        # Get exception details
        exception_msg = str(exception)
        if len(exception_msg) > 500:
            exception_msg = exception_msg[:497] + "..."
        
        # Obtenir la description du DAG
        dag_description = context["dag"].description if hasattr(context["dag"], "description") else "Aucune description disponible"
        
        # Prepare widgets for the card
        widgets = [
            {"textParagraph": {"text": f"<b>📅 Date d'exécution:</b> {execution_date}"}},
            {"textParagraph": {"text": f"<b>❌ Statut:</b> Échec"}},
            {"textParagraph": {"text": f"<b>🔍 Tâche en échec:</b> {task_id}"}},
            {"textParagraph": {"text": f"<b>📝 Description:</b> {dag_description}"}},
            {"textParagraph": {"text": f"<b>🔢 Tentative:</b> {try_number} sur {max_tries}"}},
            {"textParagraph": {"text": f"<b>⏱️ Temps d'exécution:</b> {execution_time_str}"}},
            {"textParagraph": {"text": f"<b>🕒 Heure de départ:</b> {start_date.strftime('%H:%M:%S') if start_date else 'Non disponible'}"}},
            {"textParagraph": {"text": f"<b>🕕 Heure d'échec:</b> {end_date.strftime('%H:%M:%S')}"}},
            {"textParagraph": {"text": f"<b>⚠️ Erreur:</b> {exception_msg}"}}
        ]
        
        # Get Google Chat webhook URL from Airflow connection
        conn = BaseHook.get_connection(GCHAT_CONNECTION)
        webhook_url = conn.host
        if not webhook_url.startswith('http'):
            webhook_url = f"https://{webhook_url}"
            
        # Create a unique thread ID for this DAG run
        thread_id = f"{dag_id}_{context['execution_date'].strftime('%Y%m%d')}"
        
        # Prepare the card body
        body = {
            'cardsV2': [{
                'cardId': f"{dag_id}_failure_alert",
                'card': {
                    'header': {
                        'title': f"DAG: {dag_id} {context['execution_date'].strftime('%Y-%m-%d')}",
                        'subtitle': "Exécution échouée",
                        'imageUrl': "https://img.icons8.com/color/48/cancel--v1.png"
                    },
                    'sections': [
                        {
                            'widgets': widgets
                        }
                    ]
                }
            }]
        }
        
        # Add thread parameters to the URL
        if '?' not in webhook_url:
            thread_ref = f"?threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
        else:
            thread_ref = f"&threadKey={thread_id}&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
            
        full_url = f"{webhook_url}{thread_ref}"
        
        # Send the request
        response = requests.post(full_url, json=body)
        response.raise_for_status()
        logging.info(f"Successfully sent Google Chat failure alert for DAG {dag_id}")
        
    except Exception as e:
        logging.error(f"Failed to send Google Chat failure alert: {str(e)}")
        if 'response' in locals():
            logging.error(f"Response content: {getattr(response, 'text', 'No response')}")
