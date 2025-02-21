from .models import Conversation
from rest_framework.response import Response
from core.models import User
from .serializers import ConversationListSerializer, ConversationSerializer
from django.db.models import Q
from django.shortcuts import redirect, reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.utils import IntegrityError


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_conversation(request, ):
    """
    {
        "phone_number": "09353220545"
    }
    """
    data = request.data
    print(data)
    phone_number = data.pop('phone_number')
    print(phone_number)
    try:
        participant = User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        return Response({'message': 'You cannot chat with a non existent user'})

    conversation = Conversation.objects.filter(Q(sender_conversation=request.user, receiver_conversation=participant) |
                                               Q(sender_conversation=participant, receiver_conversation=request.user))
    print(conversation.query)
    print('conversation', conversation)
    print('user', request.user)
    if conversation.exists():
        print('convo exist')
        return redirect(reverse('get_conversation', args=(conversation[0].id,)))
    else:
        conversation = Conversation.objects.create(id=request.user.id, sender_conversation=request.user,
                                                   receiver_conversation=participant)
        return Response(ConversationSerializer(sender_conversation=conversation).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation(request, convo_id):
    user = User.objects.get(id=request.user.id)
    if user.is_staff or user.is_superuser:
        conversation = Conversation.objects.filter(id=convo_id)
    else:
        conversation = Conversation.objects.filter(
            Q(id=convo_id) & (Q(sender_conversation=user) | Q(receiver_conversation=user))
        )
    if not conversation.exists():
        return Response({'message': 'Conversation does not exist'})
    else:
        serializer = ConversationSerializer(instance=conversation[0])
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def conversations(request):
    if request.user.is_staff or request.user.is_superuser:
        conversation_list = Conversation.objects.all()
    else:
        conversation_list = Conversation.objects.filter(Q(sender_conversation=request.user) |
                                                        Q(receiver_conversation=request.user))
    serializer = ConversationListSerializer(instance=conversation_list, many=True)
    return Response(serializer.data)
