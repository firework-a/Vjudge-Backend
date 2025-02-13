import logging

from fastapi import APIRouter, Query

from app.models import Question
from app.schemas import QuestionsResponse, QuestionResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("")
async def get_questions(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    query: str = "",
    source_id: int = 0,
    tag_ids: str = "",
    min_difficulty: int = 1,
    max_difficulty: int = 3,
) -> QuestionsResponse:
    try:
        # Build base query
        questions_query = Question.filter(
            difficulty__gte=min_difficulty,
            difficulty__lte=max_difficulty
        )
        
        logger.info(f"Base query params: min={min_difficulty}, max={max_difficulty}")
        
        # Add source filter if specified
        if source_id > 0:
            questions_query = questions_query.filter(source_id=source_id)
            logger.info(f"Added source filter: sourceId={source_id}")
        
        # Add title search if specified
        if query:
            questions_query = questions_query.filter(title__icontains=query)
            logger.info(f"Added title search: query={query}")
        
        # Add tags filter if specified
        if tag_ids:
            tag_id_list = [int(tag_id) for tag_id in tag_ids.split(",") if tag_id.isdigit()]
            if tag_id_list:
                questions_query = questions_query.filter(
                    tags__id__in=tag_id_list
                )
                logger.info(f"Added tags filter: tagIds={tag_id_list}")
        
        # Get total count
        total = await questions_query.count()
        logger.info(f"Total matching questions: {total}")
        
        # Get paginated results
        questions = await questions_query.prefetch_related(
            'source', 'tags'
        ).offset((page - 1) * size).limit(size).all()
        
        # Format response
        question_responses = []
        for q in questions:
            question_responses.append(QuestionResponse(
                id=q.id,
                title=q.title,
                difficulty=q.difficulty,
                source=q.source.name,
                tags=[tag.name for tag in q.tags]
            ))
        
        return QuestionsResponse(
            questions=question_responses,
            total=total
        )
    except Exception as e:
        logger.error(f"Error in get_questions: {str(e)}")
        raise
