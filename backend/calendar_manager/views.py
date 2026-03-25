from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime, timedelta
from .services import CalendarService
from users.models import Team


class CalendarView(APIView):
    """
    Unified calendar view combining all event types
    
    GET /api/calendar/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&filter=user|team|organization&team_id=1
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get calendar events"""
        # Parse query parameters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        filter_type = request.query_params.get('filter', 'user')
        team_id = request.query_params.get('team_id')
        event_types = request.query_params.getlist('event_types')
        
        # Validate required parameters
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate date range
        if start_date > end_date:
            return Response(
                {'error': 'start_date must be before or equal to end_date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get events based on filter type
        user = request.user
        
        if filter_type == 'user':
            # User's own calendar
            events = CalendarService.get_user_calendar(user, start_date, end_date)
        
        elif filter_type == 'team':
            # Team calendar
            if team_id:
                try:
                    team = Team.objects.get(id=team_id)
                    # Check permissions
                    if not (user.is_admin or (user.is_coach and team.coach == user) or user.team == team):
                        return Response(
                            {'error': 'You do not have permission to view this team calendar'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    events = CalendarService.get_team_calendar(team, start_date, end_date)
                except Team.DoesNotExist:
                    return Response(
                        {'error': 'Team not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif user.team:
                # Default to user's team
                events = CalendarService.get_team_calendar(user.team, start_date, end_date)
            else:
                return Response(
                    {'error': 'No team specified and user has no team'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif filter_type == 'organization':
            # Organization-wide calendar (admin/coach only)
            if not (user.is_admin or user.is_coach):
                return Response(
                    {'error': 'Only coaches and admins can view organization calendar'},
                    status=status.HTTP_403_FORBIDDEN
                )
            events = CalendarService.get_organization_calendar(start_date, end_date)
        
        else:
            return Response(
                {'error': 'Invalid filter type. Use: user, team, or organization'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter by event types if specified
        if event_types:
            events = [e for e in events if e['type'] in event_types]
        
        return Response({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'filter': filter_type,
            'event_count': len(events),
            'events': events
        })


class CalendarSummaryView(APIView):
    """
    Get calendar summary statistics
    
    GET /api/calendar/summary/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&filter=user|team|organization
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get calendar summary"""
        # Parse query parameters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        filter_type = request.query_params.get('filter', 'user')
        team_id = request.query_params.get('team_id')
        
        # Validate required parameters
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get events
        user = request.user
        
        if filter_type == 'user':
            events = CalendarService.get_user_calendar(user, start_date, end_date)
        elif filter_type == 'team':
            if team_id:
                try:
                    team = Team.objects.get(id=team_id)
                    events = CalendarService.get_team_calendar(team, start_date, end_date)
                except Team.DoesNotExist:
                    return Response({'error': 'Team not found'}, status=status.HTTP_404_NOT_FOUND)
            elif user.team:
                events = CalendarService.get_team_calendar(user.team, start_date, end_date)
            else:
                return Response({'error': 'No team specified'}, status=status.HTTP_400_BAD_REQUEST)
        elif filter_type == 'organization':
            if not (user.is_admin or user.is_coach):
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            events = CalendarService.get_organization_calendar(start_date, end_date)
        else:
            return Response({'error': 'Invalid filter type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate summary statistics
        summary = {
            'total_events': len(events),
            'by_type': {},
            'by_user': {},
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': (end_date - start_date).days + 1
            }
        }
        
        # Count by type
        for event in events:
            event_type = event['type']
            summary['by_type'][event_type] = summary['by_type'].get(event_type, 0) + 1
            
            # Count by user (if user info available)
            if 'user' in event and event['user']:
                user_name = event['user']['name']
                if user_name not in summary['by_user']:
                    summary['by_user'][user_name] = {
                        'total': 0,
                        'by_type': {}
                    }
                summary['by_user'][user_name]['total'] += 1
                summary['by_user'][user_name]['by_type'][event_type] = \
                    summary['by_user'][user_name]['by_type'].get(event_type, 0) + 1
        
        return Response(summary)

# Made with Bob
