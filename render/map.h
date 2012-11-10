#ifndef __MAP_H__
#define __MAP_H__

/* in-memory structures */

struct mvert_s
{
    float x, y, z;
};

struct mplane_s
{
    float normal[3];
    float dist;
    unsigned char type;
    unsigned char signbits;
    unsigned char pad[2];
};

struct medge_s
{
    unsigned short verts[2];
    unsigned int cached;
};

struct msurface_s
{
    struct mplane_s *plane;

    /* the surface's edge list is a sub-slice of surf_edges */
    unsigned int *edges;
    int num_edges;

    struct mtexinfo_s *texinfo;
};

#define NODEFLAGS_LEAF 0x80000000

struct mnode_s
{
    /* shared with leaf structure */
    unsigned int flags;
    float mins[3];
    float maxs[3];

    /* specific to node */
    void *children[2]; /* could be node or leaf */
    struct mplane_s *plane;
};

struct mleaf_s
{
    /* shared with node structure */
    unsigned int flags;
    float mins[3];
    float maxs[3];

    /* specific to leaf */
    struct msurface_s *surfs;
    int num_surfs;

    //TODO: light value, light style
};

struct mtexinfo_s
{
    int xoff, yoff;
    struct mtex_s *tex;
};

struct mtex_s
{
    int w, h;
    int has_transparent;
    unsigned char *pixels[4]; /* all mip levels */
};

struct mthing_s
{
    float pos[3];
    float angle;
    int type;
    int flags;
};

struct map_s
{
    struct mvert_s *verts;
    int num_verts;

    struct mplane_s *planes;
    int num_planes;

    struct medge_s *edges;
    int num_edges;

    struct msurface_s *surfs;
    int num_surfs;

    struct mnode_s *nodes;
    int num_nodes;

    unsigned int *surf_edges;
    int num_surf_edges;

    struct mtexinfo_s *texinfos;
    int num_texinfos;

    struct mtex_s *textures;
    int num_textures;

    struct mthing_s *things;
    int num_things;
};

#endif /* __MAP_H__ */
