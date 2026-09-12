from database import pool


# ============================================================
# GET AUTHENTICATED USER
# ============================================================

def get_current_user(auth_session_id):

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    u.id,
                    u.username,
                    u.role
                FROM auth_sessions a
                JOIN users u
                    ON u.id = a.user_id
                WHERE a.id = %s
                  AND a.is_active = TRUE
            """, (
                auth_session_id,
            ))

            user = cur.fetchone()

    if not user:
        return None

    return {
        "id": user[0],
        "username": user[1],
        "role": user[2]
    }


# ============================================================
# CREATE TASK
# MANAGER ONLY
# ============================================================

def create_task(
    auth_session_id,
    title,
    description,
    priority="MEDIUM"
):

    priority = priority.upper()

    if priority not in [
        "LOW",
        "MEDIUM",
        "HIGH",
        "URGENT"
    ]:

        return {
            "success": False,
            "message": "Invalid priority."
        }

    user = get_current_user(
        auth_session_id
    )

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    if user["role"] != "MANAGER":

        return {
            "success": False,
            "message": (
                "Permission denied. "
                "Only managers can create "
                "owner approval tasks."
            )
        }

    if not title or not title.strip():

        return {
            "success": False,
            "message": "Task title cannot be empty."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO tasks (
                    title,
                    description,
                    created_by,
                    priority,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    'PENDING_APPROVAL'
                )
                RETURNING id, created_at
            """, (
                title.strip(),
                description.strip()
                if description
                else "",
                user["id"],
                priority
            ))

            task = cur.fetchone()

        conn.commit()

    return {
        "success": True,
        "message": "Task created successfully.",
        "task": {
            "id": task[0],
            "title": title.strip(),
            "description": (
                description.strip()
                if description
                else ""
            ),
            "priority": priority,
            "status": "PENDING_APPROVAL",
            "created_by": user["username"],
            "created_at": task[1].isoformat()
        }
    }


# ============================================================
# GET PENDING TASKS
# MANAGER / OWNER
# ============================================================

def get_pending_tasks(auth_session_id):

    user = get_current_user(
        auth_session_id
    )

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    if user["role"] not in [
        "MANAGER",
        "OWNER"
    ]:

        return {
            "success": False,
            "message": "Permission denied."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    t.id,
                    t.title,
                    t.description,
                    u.username,
                    t.priority,
                    t.status,
                    t.owner_comment,
                    t.created_at
                FROM tasks t
                JOIN users u
                    ON u.id = t.created_by
                WHERE t.status = 'PENDING_APPROVAL'
                ORDER BY
                    CASE t.priority
                        WHEN 'URGENT' THEN 1
                        WHEN 'HIGH' THEN 2
                        WHEN 'MEDIUM' THEN 3
                        WHEN 'LOW' THEN 4
                    END,
                    t.created_at ASC
            """)

            rows = cur.fetchall()

    tasks = []

    for row in rows:

        tasks.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "created_by": row[3],
            "priority": row[4],
            "status": row[5],
            "owner_comment": row[6],
            "created_at": row[7].isoformat()
        })

    return {
        "success": True,
        "pending_count": len(tasks),
        "tasks": tasks
    }


# ============================================================
# APPROVE TASK
# OWNER ONLY
# ============================================================

def approve_task(
    auth_session_id,
    task_id,
    owner_comment=""
):

    user = get_current_user(
        auth_session_id
    )

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    if user["role"] != "OWNER":

        return {
            "success": False,
            "message": (
                "Permission denied. "
                "Only the owner can approve tasks."
            )
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE tasks
                SET
                    status = 'APPROVED',
                    owner_comment = %s,
                    updated_at = CURRENT_TIMESTAMP,
                    approved_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND status = 'PENDING_APPROVAL'
                RETURNING id
            """, (
                owner_comment.strip()
                if owner_comment
                else "",
                task_id
            ))

            result = cur.fetchone()

            if not result:

                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        "Task not found or "
                        "task is no longer "
                        "pending approval."
                    )
                }

        conn.commit()

    return {
        "success": True,
        "message": "Task approved successfully.",
        "task_id": task_id,
        "status": "APPROVED",
        "owner_comment": owner_comment
    }


# ============================================================
# REJECT TASK
# OWNER ONLY
# ============================================================

def reject_task(
    auth_session_id,
    task_id,
    owner_comment
):

    user = get_current_user(
        auth_session_id
    )

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    if user["role"] != "OWNER":

        return {
            "success": False,
            "message": (
                "Permission denied. "
                "Only the owner can reject tasks."
            )
        }

    if not owner_comment or not owner_comment.strip():

        return {
            "success": False,
            "message": (
                "A rejection reason is required."
            )
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE tasks
                SET
                    status = 'REJECTED',
                    owner_comment = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND status = 'PENDING_APPROVAL'
                RETURNING id
            """, (
                owner_comment.strip(),
                task_id
            ))

            result = cur.fetchone()

            if not result:

                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        "Task not found or "
                        "task is no longer "
                        "pending approval."
                    )
                }

        conn.commit()

    return {
        "success": True,
        "message": "Task rejected successfully.",
        "task_id": task_id,
        "status": "REJECTED",
        "owner_comment": owner_comment.strip()
    }


# ============================================================
# COMPLETE TASK
# MANAGER / OWNER
# ============================================================

def complete_task(
    auth_session_id,
    task_id
):

    user = get_current_user(
        auth_session_id
    )

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    if user["role"] not in [
        "MANAGER",
        "OWNER"
    ]:

        return {
            "success": False,
            "message": "Permission denied."
        }

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE tasks
                SET
                    status = 'COMPLETED',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND status = 'APPROVED'
                RETURNING id
            """, (
                task_id,
            ))

            result = cur.fetchone()

            if not result:

                conn.rollback()

                return {
                    "success": False,
                    "message": (
                        "Task not found or "
                        "task has not been approved."
                    )
                }

        conn.commit()

    return {
        "success": True,
        "message": "Task completed successfully.",
        "task_id": task_id,
        "status": "COMPLETED"
    }


# ============================================================
# CHECK PENDING TASK ALERT
# OWNER ONLY
# ============================================================

def check_pending_task_alert(
    auth_session_id
):

    user = get_current_user(
        auth_session_id
    )

    if not user:

        return {
            "success": False,
            "message": "Authentication required."
        }

    if user["role"] != "OWNER":

        return {
            "success": False,
            "message": "Permission denied."
        }

    threshold = 5

    with pool.connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT COUNT(*)
                FROM tasks
                WHERE status = 'PENDING_APPROVAL'
            """)

            pending_count = cur.fetchone()[0]

    return {
        "success": True,
        "alert_required": (
            pending_count > threshold
        ),
        "pending_count": pending_count,
        "threshold": threshold,
        "owner_email": "sudhanshukhare021@gmail.com"
    }