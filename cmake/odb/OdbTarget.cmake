if(NOT TARGET odb::odbc)
    if(CMAKE_CROSSCOMPILING)
        find_program(ODBC_PROGRAM NAMES odb PATHS ENV PATH NO_DEFAULT_PATH)
    endif()

    if(NOT ODBC_PROGRAM)
        # TODO: update according to the platform
        find_program(ODBC_PROGRAM NAMES odb PATHS "${CMAKE_CURRENT_LIST_DIR}/../../../odb-2.4.0-i686-windows/bin")
    endif()

    if(NOT ODBC_PROGRAM)
        message(SEND_ERROR "ODB compiler is not found!")
    endif()

    get_filename_component(ODBC_PROGRAM "${ODBC_PROGRAM}" ABSOLUTE)

    set(Odb_ODBC_EXECUTABLE ${ODBC_PROGRAM} CACHE FILEPATH "The odb compiler")

    add_executable(odb::odbc IMPORTED)
    set_property(TARGET odb::odbc PROPERTY IMPORTED_LOCATION ${Odb_ODBC_EXECUTABLE})
endif()